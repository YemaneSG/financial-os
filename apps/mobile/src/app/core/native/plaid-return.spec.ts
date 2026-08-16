import { describe, expect, it, vi } from 'vitest';
import { Injector } from '@angular/core';

import {
  classifyPlaidReturnUrl,
  NATIVE_URL_BRIDGE,
  PlaidReturnCoordinator,
  type NativeUrlBridge,
  type PlaidReturnPolicy,
} from './plaid-return';

const policy: PlaidReturnPolicy = {
  completionScheme: 'dev.financialos.premium.proof',
  completionHost: 'plaid',
  completionPath: '/complete',
  oauthRedirect: {
    host: 'links.synthetic.invalid',
    path: '/plaid/oauth-return',
  },
};

function createBridge(launchUrl?: string) {
  let listener: ((url: string) => void) | undefined;
  const closeBrowser = vi.fn(async () => undefined);
  const remove = vi.fn(async () => undefined);
  const bridge: NativeUrlBridge = {
    getLaunchUrl: vi.fn(async () => launchUrl),
    addUrlOpenListener: vi.fn(async (nextListener) => {
      listener = nextListener;
      return { remove };
    }),
    closeBrowser,
  };

  return {
    bridge,
    closeBrowser,
    emit(url: string) {
      listener?.(url);
    },
    remove,
  };
}

function createCoordinator(bridge: NativeUrlBridge): PlaidReturnCoordinator {
  const injector = Injector.create({
    providers: [
      PlaidReturnCoordinator,
      { provide: NATIVE_URL_BRIDGE, useValue: bridge },
    ],
  });
  return injector.get(PlaidReturnCoordinator);
}

describe('classifyPlaidReturnUrl', () => {
  it('accepts the exact token-free completion URI', () => {
    expect(
      classifyPlaidReturnUrl(
        'dev.financialos.premium.proof://plaid/complete',
        policy,
      ),
    ).toBe('completion');
  });

  it.each([
    'dev.financialos.premium.proof://plaid/complete?token=synthetic',
    'dev.financialos.premium.proof://plaid/complete#synthetic',
    'dev.financialos.premium.proof://other/complete',
    'dev.financialos.premium.proof://plaid/other',
    'javascript:alert(1)',
    'not a URL',
  ])('rejects an unexpected completion callback: %s', (url) => {
    expect(classifyPlaidReturnUrl(url, policy)).toBeNull();
  });

  it('reduces an exact HTTPS OAuth return to a category without returning URL material', () => {
    const result = classifyPlaidReturnUrl(
      'https://links.synthetic.invalid/plaid/oauth-return?oauth_state=discarded',
      policy,
    );

    expect(result).toBe('oauth-return');
    expect(result).not.toContain('oauth_state');
  });

  it('rejects an unapproved HTTPS host or path', () => {
    expect(
      classifyPlaidReturnUrl(
        'https://other.synthetic.invalid/plaid/oauth-return',
        policy,
      ),
    ).toBeNull();
    expect(
      classifyPlaidReturnUrl(
        'https://links.synthetic.invalid/other',
        policy,
      ),
    ).toBeNull();
  });
});

describe('PlaidReturnCoordinator', () => {
  it('handles a cold-start callback as an untrusted wake-up and closes the browser', async () => {
    const harness = createBridge(
      'dev.financialos.premium.proof://plaid/complete',
    );
    const coordinator = createCoordinator(harness.bridge);

    await coordinator.start(policy);

    expect(coordinator.returnSignal()).toEqual({
      kind: 'completion',
      source: 'cold-start',
    });
    expect(harness.closeBrowser).toHaveBeenCalledOnce();
  });

  it('ignores forged callbacks and does not close the browser', async () => {
    const harness = createBridge();
    const coordinator = createCoordinator(harness.bridge);
    await coordinator.start(policy);

    harness.emit(
      'dev.financialos.premium.proof://plaid/complete?public_token=discarded',
    );
    await Promise.resolve();

    expect(coordinator.returnSignal()).toBeNull();
    expect(harness.closeBrowser).not.toHaveBeenCalled();
  });

  it('keeps the sanitized wake-up when browser closure is unavailable', async () => {
    const harness = createBridge(
      'dev.financialos.premium.proof://plaid/complete',
    );
    harness.closeBrowser.mockRejectedValueOnce(new Error('synthetic failure'));
    const coordinator = createCoordinator(harness.bridge);

    await expect(coordinator.start(policy)).resolves.toBeUndefined();
    expect(coordinator.returnSignal()).toEqual({
      kind: 'completion',
      source: 'cold-start',
    });
  });

  it('removes its native listener on stop', async () => {
    const harness = createBridge();
    const coordinator = createCoordinator(harness.bridge);
    await coordinator.start(policy);

    await coordinator.stop();

    expect(harness.remove).toHaveBeenCalledOnce();
  });
});
