import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import path from "path";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: "script-defer",
      strategies: "injectManifest",
      srcDir: "src",
      filename: "sw.ts",
      manifest: false,
      injectManifest: {
        swSrc: "src/sw.ts",
        swDest: "dist/sw.js",
        // Navigations are handled by the NetworkFirst route below. Pre-caching
        // index.html lets an old worker pin an obsolete app shell and prevents
        // urgent authentication fixes from reaching existing installations.
        globPatterns: ["**/*.{js,css,svg,png,ico,woff2}"],
        globIgnores: ["**/node_modules/**", "registerSW.js"],
      },
      devOptions: {
        enabled: false,
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    target: "es2022",
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          firebase: ["firebase/app", "firebase/auth"],
          react: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
});
