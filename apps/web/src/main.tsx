import { getCanonicalFirebaseUrl } from "./auth/canonicalHost";

const canonicalUrl = getCanonicalFirebaseUrl(window.location.href);

if (canonicalUrl) {
  window.location.replace(canonicalUrl);
} else {
  void import("./bootstrap").then(({ renderApp }) => renderApp());
}
