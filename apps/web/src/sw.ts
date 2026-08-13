/// <reference lib="webworker" />
import { clientsClaim } from "workbox-core";
import { precacheAndRoute, cleanupOutdatedCaches } from "workbox-precaching";
import { registerRoute, NavigationRoute } from "workbox-routing";
import { NetworkFirst, CacheFirst, NetworkOnly } from "workbox-strategies";
import { CacheableResponsePlugin } from "workbox-cacheable-response";
import { ExpirationPlugin } from "workbox-expiration";

declare const self: ServiceWorkerGlobalScope & typeof globalThis;

clientsClaim();
self.skipWaiting();

cleanupOutdatedCaches();

// Injected by vite-plugin-pwa — app shell static assets only (JS, CSS, HTML, icons).
// APP-02: authenticated API responses, receipt images, and signed URLs are never precached.
precacheAndRoute(self.__WB_MANIFEST);

// Explicitly never cache /api/ or /internal/ routes (APP-02, OBJ-02).
registerRoute(
  ({ url }) =>
    url.pathname.startsWith("/api/") || url.pathname.startsWith("/internal/"),
  new NetworkOnly(),
);

// Static assets: long-lived cache.
registerRoute(
  ({ request, url }) =>
    url.origin === self.location.origin &&
    (request.destination === "font" || request.destination === "image"),
  new CacheFirst({
    cacheName: "static-assets-v1",
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxAgeSeconds: 60 * 60 * 24 * 30 }),
    ],
  }),
);

// Navigation: network-first so updates land quickly.
registerRoute(
  new NavigationRoute(
    new NetworkFirst({
      // v2 invalidates documents cached before signed GCS receipt images were
      // admitted by the exact-origin CSP.
      cacheName: "app-shell-v2",
      plugins: [
        new CacheableResponsePlugin({ statuses: [200] }),
        new ExpirationPlugin({ maxAgeSeconds: 60 * 60 * 24 }),
      ],
    }),
  ),
);

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") {
    void self.skipWaiting();
  }
});
