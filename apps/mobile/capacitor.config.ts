import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'dev.financialos.premium.proof',
  appName: 'Financial OS PM-0A',
  webDir: 'dist/financial-os-mobile/browser',
  server: {
    androidScheme: 'https',
  },
};

export default config;
