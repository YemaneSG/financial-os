export interface OwnerPredicateResult {
  readonly active: boolean;
  readonly error: boolean;
}

export interface OwnerPredicateClient {
  evaluate(): Promise<OwnerPredicateResult>;
}

export type OwnerPredicateClientFactory = (
  authorization: string,
) => OwnerPredicateClient;

const JSON_HEADERS = {
  'cache-control': 'no-store',
  'content-type': 'application/json; charset=utf-8',
} as const;

function jsonError(status: number, code: string): Response {
  return new Response(JSON.stringify({ code }), {
    status,
    headers: JSON_HEADERS,
  });
}

export async function handleOwnerAuthorizationProbe(
  request: Request,
  createClient: OwnerPredicateClientFactory,
): Promise<Response> {
  if (request.method !== 'POST') {
    return new Response(null, {
      status: 405,
      headers: {
        allow: 'POST',
        'cache-control': 'no-store',
      },
    });
  }

  const authorization = request.headers.get('authorization');
  if (!authorization || !/^Bearer [^\s]+$/.test(authorization)) {
    return jsonError(401, 'authentication_required');
  }

  const result = await createClient(authorization).evaluate();
  if (result.error) {
    return jsonError(503, 'authorization_unavailable');
  }

  if (!result.active) {
    return jsonError(403, 'owner_required');
  }

  return new Response(null, {
    status: 204,
    headers: {
      'cache-control': 'no-store',
    },
  });
}
