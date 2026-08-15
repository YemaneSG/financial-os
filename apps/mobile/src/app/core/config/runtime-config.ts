export interface PremiumMobileRuntimeConfig {
  readonly firebase: {
    readonly apiKey: string;
    readonly appId: string;
    readonly authDomain: string;
    readonly projectId: string;
  };
  readonly supabase: {
    readonly publishableKey: string;
    readonly url: string;
  };
}

declare global {
  // Values are injected privately at runtime; no real project identifiers belong in source.
  var __FINANCIAL_OS_PREMIUM_CONFIG__: PremiumMobileRuntimeConfig | undefined;
}

export function readRuntimeConfig(): PremiumMobileRuntimeConfig {
  const config = globalThis.__FINANCIAL_OS_PREMIUM_CONFIG__;

  if (!config) {
    throw new Error('Premium mobile runtime configuration is unavailable.');
  }

  return config;
}
