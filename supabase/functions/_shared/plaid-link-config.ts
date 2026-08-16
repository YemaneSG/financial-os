const COMPLETION_REDIRECT_URI = 'financialos://plaid/complete';
const HOSTED_LINK_LIFETIME_SECONDS = 900;

export function buildHostedLinkCreatePayload(clientUserId: string) {
  return {
    client_name: 'Financial OS',
    country_codes: ['US'],
    hosted_link: {
      completion_redirect_uri: COMPLETION_REDIRECT_URI,
      // PM-0A is the server/browser proof. Plaid requires a registered HTTPS
      // Universal/App Link in `redirect_uri` when this flag is true; that
      // native return contract is intentionally deferred to PM-0B.
      is_mobile_app: false,
      url_lifetime_seconds: HOSTED_LINK_LIFETIME_SECONDS,
    },
    language: 'en',
    products: ['transactions'],
    user: { client_user_id: clientUserId },
  };
}
