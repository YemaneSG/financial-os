export type HostedLinkState =
  | 'pending'
  | 'succeeded'
  | 'cancelled'
  | 'expired'
  | 'failed';

export type OwnerAuthorizationResult =
  | { readonly kind: 'authorized'; readonly subject: string }
  | { readonly kind: 'denied' }
  | { readonly kind: 'unavailable' };

type AuthorizedOwner = Extract<OwnerAuthorizationResult, { kind: 'authorized' }>;

export interface CreatedHostedLink {
  readonly expiration: string;
  readonly hostedLinkUrl: string;
  readonly linkToken: string;
}

export interface PlaidLinkSession {
  readonly expiration: string | null;
  readonly linkSessions: ReadonlyArray<{
    readonly finishedAt: string | null;
    readonly exited: boolean;
    readonly itemAdded: boolean;
  }>;
}

export interface PlaidGateway {
  createHostedLink(clientUserId: string): Promise<CreatedHostedLink>;
  getLinkSession(linkToken: string): Promise<PlaidLinkSession>;
}

export interface ClaimedHostedLink {
  readonly claimed: boolean;
  readonly expiresAt: string;
  readonly linkToken: string | null;
  readonly state: HostedLinkState | 'checking';
}

export interface HostedLinkStore {
  create(input: {
    readonly expiresAt: string;
    readonly linkToken: string;
    readonly ownerSubject: string;
    readonly sessionId: string;
  }): Promise<boolean>;
  claim(input: {
    readonly claimNonce: string;
    readonly now: string;
    readonly ownerSubject: string;
    readonly sessionId: string;
  }): Promise<ClaimedHostedLink | null>;
  finish(input: {
    readonly claimNonce: string;
    readonly finishedAt: string;
    readonly ownerSubject: string;
    readonly sessionId: string;
    readonly state: Exclude<HostedLinkState, 'pending'>;
  }): Promise<boolean>;
  release(input: {
    readonly claimNonce: string;
    readonly ownerSubject: string;
    readonly sessionId: string;
  }): Promise<boolean>;
}

export interface HostedLinkServerDependencies {
  readonly plaid: PlaidGateway;
  readonly store: HostedLinkStore;
}

export interface HostedLinkDependencies {
  authorize(authorization: string): Promise<OwnerAuthorizationResult>;
  createServerDependencies(subject: string): HostedLinkServerDependencies;
  now(): Date;
  randomUUID(): string;
}

const JSON_HEADERS = {
  'cache-control': 'no-store',
  'content-type': 'application/json; charset=utf-8',
} as const;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: JSON_HEADERS,
  });
}

function bearer(request: Request): string | null {
  const authorization = request.headers.get('authorization');
  return authorization && /^Bearer [^\s]+$/.test(authorization)
    ? authorization
    : null;
}

async function authorize(
  request: Request,
  dependencies: HostedLinkDependencies,
): Promise<AuthorizedOwner | Response> {
  const authorization = bearer(request);
  if (!authorization) {
    return json(401, { code: 'authentication_required' });
  }

  const result = await dependencies.authorize(authorization);
  if (result.kind === 'unavailable') {
    return json(503, { code: 'authorization_unavailable' });
  }
  if (result.kind === 'denied') {
    return json(403, { code: 'owner_required' });
  }
  return result;
}

function isResponse(value: AuthorizedOwner | Response): value is Response {
  return value instanceof Response;
}

async function readSessionId(request: Request): Promise<string | null> {
  const declaredLength = request.headers.get('content-length');
  if (declaredLength && Number(declaredLength) > 512) {
    return null;
  }

  const reader = request.body?.getReader();
  if (!reader) {
    return null;
  }

  const decoder = new TextDecoder();
  let raw = '';
  let receivedBytes = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      raw += decoder.decode();
      break;
    }
    receivedBytes += value.byteLength;
    if (receivedBytes > 512) {
      await reader.cancel();
      return null;
    }
    raw += decoder.decode(value, { stream: true });
  }

  if (raw.length === 0) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      typeof parsed !== 'object' ||
      parsed === null ||
      !('session_id' in parsed) ||
      typeof parsed.session_id !== 'string' ||
      !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
        parsed.session_id,
      )
    ) {
      return null;
    }
    return parsed.session_id;
  } catch {
    return null;
  }
}

function classifyPlaidSession(
  session: PlaidLinkSession,
  now: Date,
): HostedLinkState {
  if (session.expiration && new Date(session.expiration).getTime() <= now.getTime()) {
    return 'expired';
  }

  const completed = session.linkSessions.filter((item) => item.finishedAt);
  if (completed.some((item) => item.itemAdded)) {
    return 'succeeded';
  }
  if (completed.length === 0) {
    return 'pending';
  }
  if (completed.some((item) => item.exited)) {
    return 'cancelled';
  }
  return 'failed';
}

export async function handleHostedLinkCreate(
  request: Request,
  dependencies: HostedLinkDependencies,
): Promise<Response> {
  if (request.method !== 'POST') {
    return new Response(null, {
      status: 405,
      headers: { allow: 'POST', 'cache-control': 'no-store' },
    });
  }

  const authorization = await authorize(request, dependencies);
  if (isResponse(authorization)) {
    return authorization;
  }

  try {
    const server = dependencies.createServerDependencies(authorization.subject);
    const sessionId = dependencies.randomUUID();
    const created = await server.plaid.createHostedLink(`pm0-${sessionId}`);
    const persisted = await server.store.create({
      expiresAt: created.expiration,
      linkToken: created.linkToken,
      ownerSubject: authorization.subject,
      sessionId,
    });

    if (!persisted) {
      return json(503, { code: 'link_session_unavailable' });
    }

    return json(201, {
      expires_at: created.expiration,
      hosted_link_url: created.hostedLinkUrl,
      session_id: sessionId,
    });
  } catch {
    return json(503, { code: 'link_session_unavailable' });
  }
}

export async function handleHostedLinkStatus(
  request: Request,
  dependencies: HostedLinkDependencies,
): Promise<Response> {
  if (request.method !== 'POST') {
    return new Response(null, {
      status: 405,
      headers: { allow: 'POST', 'cache-control': 'no-store' },
    });
  }

  const authorization = await authorize(request, dependencies);
  if (isResponse(authorization)) {
    return authorization;
  }

  const sessionId = await readSessionId(request);
  if (!sessionId) {
    return json(400, { code: 'invalid_request' });
  }

  let server: HostedLinkServerDependencies;
  let claimNonce: string;
  let now: Date;
  let claimed: ClaimedHostedLink | null;
  try {
    server = dependencies.createServerDependencies(authorization.subject);
    claimNonce = dependencies.randomUUID();
    now = dependencies.now();
    claimed = await server.store.claim({
      claimNonce,
      now: now.toISOString(),
      ownerSubject: authorization.subject,
      sessionId,
    });
  } catch {
    return json(503, { code: 'link_session_unavailable' });
  }

  if (!claimed) {
    return json(404, { code: 'link_session_not_found' });
  }
  if (!claimed.claimed || !claimed.linkToken) {
    const state = claimed.state === 'checking' ? 'pending' : claimed.state;
    return json(200, { state });
  }

  try {
    const plaidSession = await server.plaid.getLinkSession(claimed.linkToken);
    const state = classifyPlaidSession(plaidSession, now);

    if (state === 'pending') {
      await server.store.release({
        claimNonce,
        ownerSubject: authorization.subject,
        sessionId,
      });
      return json(200, { state });
    }

    const finished = await server.store.finish({
      claimNonce,
      finishedAt: now.toISOString(),
      ownerSubject: authorization.subject,
      sessionId,
      state,
    });
    if (!finished) {
      return json(503, { code: 'link_session_unavailable' });
    }
    return json(200, { state });
  } catch {
    try {
      await server.store.release({
        claimNonce,
        ownerSubject: authorization.subject,
        sessionId,
      });
    } catch {
      // The fixed response below is authoritative; the lease expires in 30 seconds.
    }
    return json(503, { code: 'plaid_unavailable' });
  }
}
