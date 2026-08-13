const WEB_APP_SUFFIX = ".web.app";
const FIREBASE_APP_SUFFIX = ".firebaseapp.com";

/**
 * Firebase redirect authentication requires the app and auth helper to share
 * an origin in browsers that partition third-party storage. Firebase Hosting
 * exposes equivalent web.app and firebaseapp.com aliases, while this app's
 * configured authDomain uses firebaseapp.com. Canonicalize before Firebase is
 * initialized so redirect state remains first-party on Safari and Chrome.
 */
export function getCanonicalFirebaseUrl(currentUrl: string): string | null {
  const url = new URL(currentUrl);
  const hostname = url.hostname.toLowerCase();

  if (!hostname.endsWith(WEB_APP_SUFFIX)) {
    return null;
  }

  const siteName = hostname.slice(0, -WEB_APP_SUFFIX.length);
  if (!siteName || siteName.includes(".")) {
    return null;
  }

  url.protocol = "https:";
  url.hostname = `${siteName}${FIREBASE_APP_SUFFIX}`;
  url.port = "";
  return url.toString();
}
