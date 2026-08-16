import { createClient, type SupabaseClient } from '@supabase/supabase-js';

import {
  type ClaimedHostedLink,
  type HostedLinkDependencies,
  type HostedLinkStore,
  type PlaidGateway,
  type PlaidLinkSession,
} from './plaid-hosted-link.ts';
import { buildHostedLinkCreatePayload } from './plaid-link-config.ts';

const PLAID_BASE_URL = 'https://sandbox.plaid.com';

function requiredEnvironment(name: string): string {
  const value = Deno.env.get(name);
  if (!value) {
    throw new Error(`Missing required environment: ${name}`);
  }
  return value;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

class SandboxPlaidGateway implements PlaidGateway {
  private readonly clientId: string;
  private readonly nativeRedirectUri: string | undefined;
  private readonly secret: string;

  constructor(
    clientId: string,
    secret: string,
    nativeRedirectUri: string | undefined,
  ) {
    this.clientId = clientId;
    this.secret = secret;
    this.nativeRedirectUri = nativeRedirectUri;
  }

  private async post(path: string, body: unknown): Promise<unknown> {
    const response = await fetch(`${PLAID_BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'PLAID-CLIENT-ID': this.clientId,
        'PLAID-SECRET': this.secret,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(10_000),
    });

    if (!response.ok) {
      throw new Error('Plaid request failed');
    }
    return await response.json();
  }

  async createHostedLink(clientUserId: string) {
    const payload = await this.post(
      '/link/token/create',
      buildHostedLinkCreatePayload(clientUserId, this.nativeRedirectUri),
    );

    if (
      !isRecord(payload) ||
      typeof payload.expiration !== 'string' ||
      typeof payload.hosted_link_url !== 'string' ||
      typeof payload.link_token !== 'string' ||
      !payload.link_token.startsWith('link-sandbox-') ||
      !Number.isFinite(Date.parse(payload.expiration))
    ) {
      throw new Error('Unexpected Plaid response');
    }

    const hostedLinkUrl = new URL(payload.hosted_link_url);
    if (
      hostedLinkUrl.protocol !== 'https:' ||
      hostedLinkUrl.hostname !== 'secure.plaid.com'
    ) {
      throw new Error('Unexpected Plaid response');
    }

    return {
      expiration: payload.expiration,
      hostedLinkUrl: hostedLinkUrl.toString(),
      linkToken: payload.link_token,
    };
  }

  async getLinkSession(linkToken: string): Promise<PlaidLinkSession> {
    const payload = await this.post('/link/token/get', {
      link_token: linkToken,
    });
    if (!isRecord(payload)) {
      throw new Error('Unexpected Plaid response');
    }

    const rawSessions = Array.isArray(payload.link_sessions)
      ? payload.link_sessions
      : [];
    const linkSessions = rawSessions.filter(isRecord).map((session) => {
      const results = isRecord(session.results) ? session.results : null;
      const itemAdds = results && Array.isArray(results.item_add_results)
        ? results.item_add_results
        : [];
      const legacySuccess = isRecord(session.on_success) &&
        typeof session.on_success.public_token === 'string';

      return {
        finishedAt: typeof session.finished_at === 'string'
          ? session.finished_at
          : null,
        exited: isRecord(session.exit) || isRecord(session.on_exit),
        itemAdded: itemAdds.length > 0 || legacySuccess,
      };
    });

    const expiration = typeof payload.expiration === 'string' &&
        Number.isFinite(Date.parse(payload.expiration))
      ? payload.expiration
      : null;

    return {
      expiration,
      linkSessions,
    };
  }
}

function storeFor(serviceClient: SupabaseClient): HostedLinkStore {
  return {
    async create(input) {
      const { data, error } = await serviceClient.rpc(
        'pm0_store_plaid_link_session',
        {
          p_expires_at: input.expiresAt,
          p_link_token: input.linkToken,
          p_owner_subject: input.ownerSubject,
          p_session_id: input.sessionId,
        },
      );
      return error === null && data === true;
    },
    async claim(input): Promise<ClaimedHostedLink | null> {
      const { data, error } = await serviceClient.rpc(
        'pm0_claim_plaid_link_session',
        {
          p_claim_nonce: input.claimNonce,
          p_now: input.now,
          p_owner_subject: input.ownerSubject,
          p_session_id: input.sessionId,
        },
      );
      if (error || !Array.isArray(data) || data.length === 0) {
        return null;
      }

      const row = data[0] as Record<string, unknown>;
      if (
        typeof row.claimed !== 'boolean' ||
        typeof row.expires_at !== 'string' ||
        typeof row.state !== 'string' ||
        ![
          'pending',
          'checking',
          'succeeded',
          'cancelled',
          'expired',
          'failed',
        ].includes(row.state) ||
        !(row.link_token === null || typeof row.link_token === 'string')
      ) {
        return null;
      }

      return {
        claimed: row.claimed,
        expiresAt: row.expires_at,
        linkToken: row.link_token,
        state: row.state as ClaimedHostedLink['state'],
      };
    },
    async finish(input) {
      const { data, error } = await serviceClient.rpc(
        'pm0_finish_plaid_link_session',
        {
          p_claim_nonce: input.claimNonce,
          p_finished_at: input.finishedAt,
          p_owner_subject: input.ownerSubject,
          p_session_id: input.sessionId,
          p_state: input.state,
        },
      );
      return error === null && data === true;
    },
    async release(input) {
      const { data, error } = await serviceClient.rpc(
        'pm0_release_plaid_link_session',
        {
          p_claim_nonce: input.claimNonce,
          p_owner_subject: input.ownerSubject,
          p_session_id: input.sessionId,
        },
      );
      return error === null && data === true;
    },
  };
}

export function createHostedLinkDependencies(): HostedLinkDependencies {
  return {
    async authorize(authorization) {
      try {
        const supabaseUrl = requiredEnvironment('SUPABASE_URL');
        const publishableKey = requiredEnvironment('SUPABASE_ANON_KEY');
        const caller = createClient(supabaseUrl, publishableKey, {
          auth: {
            autoRefreshToken: false,
            detectSessionInUrl: false,
            persistSession: false,
          },
          global: { headers: { Authorization: authorization } },
        });
        const { data, error } = await caller.rpc('pm0_active_owner_subject');

        if (error) {
          return { kind: 'unavailable' };
        }
        return typeof data === 'string' && data.length > 0
          ? { kind: 'authorized', subject: data }
          : { kind: 'denied' };
      } catch {
        return { kind: 'unavailable' };
      }
    },
    createServerDependencies() {
      const supabaseUrl = requiredEnvironment('SUPABASE_URL');
      const serviceRoleKey = requiredEnvironment('SUPABASE_SERVICE_ROLE_KEY');
      const serviceClient = createClient(supabaseUrl, serviceRoleKey, {
        auth: {
          autoRefreshToken: false,
          detectSessionInUrl: false,
          persistSession: false,
        },
      });

      return {
        plaid: new SandboxPlaidGateway(
          requiredEnvironment('PLAID_CLIENT_ID'),
          requiredEnvironment('PLAID_SECRET'),
          Deno.env.get('PLAID_NATIVE_REDIRECT_URI') || undefined,
        ),
        store: storeFor(serviceClient),
      };
    },
    now() {
      return new Date();
    },
    randomUUID() {
      return crypto.randomUUID();
    },
  };
}
