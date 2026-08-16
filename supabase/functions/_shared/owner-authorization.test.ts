import assert from 'node:assert/strict';
import test from 'node:test';

import {
  handleOwnerAuthorizationProbe,
  type OwnerPredicateClientFactory,
} from './owner-authorization.ts';

const ENDPOINT = 'https://synthetic.invalid/functions/v1/pm0-auth-probe';

function factoryFor(
  active: boolean,
  error = false,
  onCreate?: (authorization: string) => void,
): OwnerPredicateClientFactory {
  return (authorization) => {
    onCreate?.(authorization);
    return {
      async evaluate() {
        return { active, error };
      },
    };
  };
}

test('rejects methods other than POST before authorization', async () => {
  const response = await handleOwnerAuthorizationProbe(
    new Request(ENDPOINT, { method: 'GET' }),
    () => {
      throw new Error('client factory must not run');
    },
  );

  assert.equal(response.status, 405);
  assert.equal(response.headers.get('allow'), 'POST');
});

test('rejects a missing bearer token before creating a client', async () => {
  const response = await handleOwnerAuthorizationProbe(
    new Request(ENDPOINT, { method: 'POST' }),
    () => {
      throw new Error('client factory must not run');
    },
  );

  assert.equal(response.status, 401);
  assert.deepEqual(await response.json(), { code: 'authentication_required' });
});

test('rejects a malformed bearer token before creating a client', async () => {
  const response = await handleOwnerAuthorizationProbe(
    new Request(ENDPOINT, {
      method: 'POST',
      headers: { authorization: 'Bearer not valid' },
    }),
    () => {
      throw new Error('client factory must not run');
    },
  );

  assert.equal(response.status, 401);
});

test('passes the unchanged bearer header to the caller-scoped client', async () => {
  let observedAuthorization = '';
  const response = await handleOwnerAuthorizationProbe(
    new Request(ENDPOINT, {
      method: 'POST',
      headers: { authorization: 'Bearer synthetic-token' },
    }),
    factoryFor(true, false, (authorization) => {
      observedAuthorization = authorization;
    }),
  );

  assert.equal(response.status, 204);
  assert.equal(observedAuthorization, 'Bearer synthetic-token');
  assert.equal(response.headers.get('cache-control'), 'no-store');
});

test('denies a caller when the common owner predicate is false', async () => {
  const response = await handleOwnerAuthorizationProbe(
    new Request(ENDPOINT, {
      method: 'POST',
      headers: { authorization: 'Bearer synthetic-token' },
    }),
    factoryFor(false),
  );

  assert.equal(response.status, 403);
  assert.deepEqual(await response.json(), { code: 'owner_required' });
});

test('fails closed without leaking predicate errors', async () => {
  const response = await handleOwnerAuthorizationProbe(
    new Request(ENDPOINT, {
      method: 'POST',
      headers: { authorization: 'Bearer synthetic-token' },
    }),
    factoryFor(false, true),
  );

  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { code: 'authorization_unavailable' });
});
