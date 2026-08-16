import { readRuntimeConfig } from './runtime-config';

describe('readRuntimeConfig', () => {
  afterEach(() => {
    globalThis.__FINANCIAL_OS_PREMIUM_CONFIG__ = undefined;
  });

  it('fails closed when private runtime configuration is absent', () => {
    expect(() => readRuntimeConfig()).toThrowError(
      'Premium mobile runtime configuration is unavailable.',
    );
  });

  it('returns injected runtime configuration without repository defaults', () => {
    const config = {
      firebase: {
        apiKey: 'synthetic-api-key',
        appId: 'synthetic-app-id',
        authDomain: 'synthetic.invalid',
        projectId: 'synthetic-project',
      },
      supabase: {
        publishableKey: 'synthetic-publishable-key',
        url: 'https://synthetic.invalid',
      },
    } as const;
    globalThis.__FINANCIAL_OS_PREMIUM_CONFIG__ = config;

    expect(readRuntimeConfig()).toBe(config);
  });
});
