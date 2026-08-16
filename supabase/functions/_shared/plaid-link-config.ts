const COMPLETION_REDIRECT_URI =
  'dev.financialos.premium.proof://plaid/complete';
const HOSTED_LINK_LIFETIME_SECONDS = 900;

function validNativeRedirectUri(value: string): boolean {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'https:' &&
      parsed.hostname.length > 0 &&
      !parsed.username &&
      !parsed.password &&
      !parsed.port &&
      !parsed.search &&
      !parsed.hash;
  } catch {
    return false;
  }
}

export function buildHostedLinkCreatePayload(
  clientUserId: string,
  nativeRedirectUri?: string,
) {
  if (nativeRedirectUri !== undefined && !validNativeRedirectUri(nativeRedirectUri)) {
    throw new Error('Invalid native redirect configuration');
  }

  const payload = {
    client_name: 'Financial OS',
    country_codes: ['US'],
    hosted_link: {
      completion_redirect_uri: COMPLETION_REDIRECT_URI,
      is_mobile_app: nativeRedirectUri !== undefined,
      url_lifetime_seconds: HOSTED_LINK_LIFETIME_SECONDS,
    },
    language: 'en',
    products: ['transactions'],
    user: { client_user_id: clientUserId },
  };

  return nativeRedirectUri
    ? { ...payload, redirect_uri: nativeRedirectUri }
    : payload;
}
