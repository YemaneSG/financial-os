import assert from 'node:assert/strict';
import test from 'node:test';

import {
  type ClaimedHostedLink,
  type HostedLinkDependencies,
  type HostedLinkState,
  handleHostedLinkCreate,
  handleHostedLinkStatus,
  type OwnerAuthorizationResult,
  type PlaidLinkSession,
} from './plaid-hosted-link.ts';

const ENDPOINT = 'https://synthetic.invalid/functions/v1/plaid-link';
const OWNER = 'synthetic-owner';
const SESSION_ID = '10000000-0000-4000-8000-000000000001';
const CLAIM_ID = '20000000-0000-4000-8000-000000000002';
const NOW = new Date('2026-08-15T18:00:00.000Z');
const EXPIRATION = '2026-08-15T18:15:00.000Z';

interface HarnessOptions {
  readonly authorization?: OwnerAuthorizationResult;
  readonly claim?: ClaimedHostedLink | null;
  readonly createStored?: boolean;
  readonly finishStored?: boolean;
  readonly plaidSession?: PlaidLinkSession;
  readonly plaidThrows?: boolean;
}

function harness(options: HarnessOptions = {}) {
  const observations = {
    clientUserId: '',
    createServerCalls: 0,
    finishStates: [] as HostedLinkState[],
    plaidCreateCalls: 0,
    plaidGetCalls: 0,
    releaseCalls: 0,
    storedOwner: '',
    storedToken: '',
  };

  let uuidCalls = 0;
  const dependencies: HostedLinkDependencies = {
    async authorize() {
      return options.authorization ?? { kind: 'authorized', subject: OWNER };
    },
    createServerDependencies() {
      observations.createServerCalls += 1;
      return {
        plaid: {
          async createHostedLink(clientUserId) {
            observations.plaidCreateCalls += 1;
            observations.clientUserId = clientUserId;
            return {
              expiration: EXPIRATION,
              hostedLinkUrl: 'https://secure.plaid.com/synthetic-hosted-link',
              linkToken: 'synthetic-link-token',
            };
          },
          async getLinkSession() {
            observations.plaidGetCalls += 1;
            if (options.plaidThrows) {
              throw new Error('synthetic Plaid failure');
            }
            return options.plaidSession ?? {
              expiration: EXPIRATION,
              linkSessions: [],
            };
          },
        },
        store: {
          async create(input) {
            observations.storedOwner = input.ownerSubject;
            observations.storedToken = input.linkToken;
            return options.createStored ?? true;
          },
          async claim() {
            return options.claim === undefined
              ? {
                  claimed: true,
                  expiresAt: EXPIRATION,
                  linkToken: 'synthetic-link-token',
                  state: 'checking',
                }
              : options.claim;
          },
          async finish(input) {
            observations.finishStates.push(input.state);
            return options.finishStored ?? true;
          },
          async release() {
            observations.releaseCalls += 1;
            return true;
          },
        },
      };
    },
    now() {
      return NOW;
    },
    randomUUID() {
      uuidCalls += 1;
      return uuidCalls === 1 ? SESSION_ID : CLAIM_ID;
    },
  };

  return { dependencies, observations };
}

function post(body?: unknown, authorization = true): Request {
  return new Request(ENDPOINT, {
    method: 'POST',
    headers: {
      ...(authorization ? { authorization: 'Bearer synthetic-token' } : {}),
      ...(body === undefined ? {} : { 'content-type': 'application/json' }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

test('rejects unsupported methods before authorization or server access', async () => {
  const { dependencies, observations } = harness();
  const response = await handleHostedLinkCreate(
    new Request(ENDPOINT, { method: 'GET' }),
    dependencies,
  );

  assert.equal(response.status, 405);
  assert.equal(observations.createServerCalls, 0);
});

test('rejects missing authentication before server dependencies exist', async () => {
  const { dependencies, observations } = harness();
  const response = await handleHostedLinkCreate(post(undefined, false), dependencies);

  assert.equal(response.status, 401);
  assert.equal(observations.createServerCalls, 0);
});

test('denies a non-owner before Plaid or service-role access exists', async () => {
  const { dependencies, observations } = harness({
    authorization: { kind: 'denied' },
  });
  const response = await handleHostedLinkCreate(post(), dependencies);

  assert.equal(response.status, 403);
  assert.equal(observations.createServerCalls, 0);
  assert.equal(observations.plaidCreateCalls, 0);
});

test('creates and stores a subject-bound session without exposing its link token', async () => {
  const { dependencies, observations } = harness();
  const response = await handleHostedLinkCreate(post(), dependencies);
  const body = await response.json();

  assert.equal(response.status, 201);
  assert.equal(body.session_id, SESSION_ID);
  assert.equal(
    body.hosted_link_url,
    'https://secure.plaid.com/synthetic-hosted-link',
  );
  assert.equal(body.link_token, undefined);
  assert.equal(observations.storedOwner, OWNER);
  assert.equal(observations.storedToken, 'synthetic-link-token');
  assert.equal(observations.clientUserId, `pm0-${SESSION_ID}`);
  assert.equal(observations.clientUserId.includes(OWNER), false);
});

test('does not return an unpersisted Hosted Link capability', async () => {
  const { dependencies } = harness({ createStored: false });
  const response = await handleHostedLinkCreate(post(), dependencies);

  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { code: 'link_session_unavailable' });
});

test('rejects a forged session identifier before server access', async () => {
  const { dependencies, observations } = harness();
  const response = await handleHostedLinkStatus(
    post({ session_id: 'not-a-session' }),
    dependencies,
  );

  assert.equal(response.status, 400);
  assert.equal(observations.createServerCalls, 0);
});

test('rejects an oversized status body before server access', async () => {
  const { dependencies, observations } = harness();
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID, padding: 'x'.repeat(600) }),
    dependencies,
  );

  assert.equal(response.status, 400);
  assert.equal(observations.createServerCalls, 0);
});

test('hides cross-subject and missing sessions behind the same 404', async () => {
  const { dependencies, observations } = harness({ claim: null });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.equal(response.status, 404);
  assert.deepEqual(await response.json(), { code: 'link_session_not_found' });
  assert.equal(observations.plaidGetCalls, 0);
});

test('returns a duplicate in-flight claim as pending without a second Plaid call', async () => {
  const { dependencies, observations } = harness({
    claim: {
      claimed: false,
      expiresAt: EXPIRATION,
      linkToken: null,
      state: 'checking',
    },
  });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.deepEqual(await response.json(), { state: 'pending' });
  assert.equal(observations.plaidGetCalls, 0);
});

test('returns a terminal replay without querying Plaid again', async () => {
  const { dependencies, observations } = harness({
    claim: {
      claimed: false,
      expiresAt: EXPIRATION,
      linkToken: null,
      state: 'succeeded',
    },
  });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.deepEqual(await response.json(), { state: 'succeeded' });
  assert.equal(observations.plaidGetCalls, 0);
});

test('keeps an unfinished session pending and releases its polling claim', async () => {
  const { dependencies, observations } = harness();
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.deepEqual(await response.json(), { state: 'pending' });
  assert.equal(observations.releaseCalls, 1);
  assert.deepEqual(observations.finishStates, []);
});

test('records success without returning or persisting Plaid result details', async () => {
  const { dependencies, observations } = harness({
    plaidSession: {
      expiration: EXPIRATION,
      linkSessions: [
        { finishedAt: NOW.toISOString(), exited: false, itemAdded: true },
      ],
    },
  });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );
  const body = await response.json();

  assert.deepEqual(body, { state: 'succeeded' });
  assert.equal(JSON.stringify(body).includes('token'), false);
  assert.deepEqual(observations.finishStates, ['succeeded']);
});

test('preserves success when a later session attempt remains unfinished', async () => {
  const { dependencies, observations } = harness({
    plaidSession: {
      expiration: EXPIRATION,
      linkSessions: [
        { finishedAt: NOW.toISOString(), exited: false, itemAdded: true },
        { finishedAt: null, exited: false, itemAdded: false },
      ],
    },
  });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.deepEqual(await response.json(), { state: 'succeeded' });
  assert.deepEqual(observations.finishStates, ['succeeded']);
});

test('records a finished exit as cancelled', async () => {
  const { dependencies, observations } = harness({
    plaidSession: {
      expiration: EXPIRATION,
      linkSessions: [
        { finishedAt: NOW.toISOString(), exited: true, itemAdded: false },
      ],
    },
  });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.deepEqual(await response.json(), { state: 'cancelled' });
  assert.deepEqual(observations.finishStates, ['cancelled']);
});

test('records Plaid expiration without interpreting the mobile callback', async () => {
  const { dependencies, observations } = harness({
    plaidSession: {
      expiration: '2026-08-15T17:59:59.000Z',
      linkSessions: [],
    },
  });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.deepEqual(await response.json(), { state: 'expired' });
  assert.deepEqual(observations.finishStates, ['expired']);
});

test('releases a polling claim and fails closed when Plaid is unavailable', async () => {
  const { dependencies, observations } = harness({ plaidThrows: true });
  const response = await handleHostedLinkStatus(
    post({ session_id: SESSION_ID }),
    dependencies,
  );

  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { code: 'plaid_unavailable' });
  assert.equal(observations.releaseCalls, 1);
});
