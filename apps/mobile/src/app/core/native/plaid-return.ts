import { inject, Injectable, InjectionToken, signal } from '@angular/core';
import { App as CapacitorApp } from '@capacitor/app';
import { Browser } from '@capacitor/browser';
import type { PluginListenerHandle } from '@capacitor/core';

export type PlaidReturnKind = 'completion' | 'oauth-return';
export type PlaidReturnSource = 'cold-start' | 'resume';

export interface PlaidReturnSignal {
  readonly kind: PlaidReturnKind;
  readonly source: PlaidReturnSource;
}

export interface PlaidReturnPolicy {
  readonly completionScheme: string;
  readonly completionHost: string;
  readonly completionPath: string;
  readonly oauthRedirect?: {
    readonly host: string;
    readonly path: string;
  };
}

export interface NativeUrlBridge {
  getLaunchUrl(): Promise<string | undefined>;
  addUrlOpenListener(
    listener: (url: string) => void,
  ): Promise<PluginListenerHandle>;
  closeBrowser(): Promise<void>;
}

export const PLAID_RETURN_POLICY: PlaidReturnPolicy = {
  completionScheme: 'dev.financialos.premium.proof',
  completionHost: 'plaid',
  completionPath: '/complete',
};

const capacitorNativeUrlBridge: NativeUrlBridge = {
  async getLaunchUrl() {
    const launch = await CapacitorApp.getLaunchUrl();
    return launch?.url;
  },
  addUrlOpenListener(listener) {
    return CapacitorApp.addListener('appUrlOpen', ({ url }) => listener(url));
  },
  closeBrowser() {
    return Browser.close();
  },
};

export const NATIVE_URL_BRIDGE = new InjectionToken<NativeUrlBridge>(
  'NATIVE_URL_BRIDGE',
  {
    providedIn: 'root',
    factory: () => capacitorNativeUrlBridge,
  },
);

/**
 * Reduces an untrusted native URL to a privacy-safe wake-up category.
 * The raw URL and all query/fragment material are deliberately discarded.
 */
export function classifyPlaidReturnUrl(
  rawUrl: string,
  policy: PlaidReturnPolicy,
): PlaidReturnKind | null {
  if (!rawUrl || rawUrl.length > 2048) {
    return null;
  }

  let parsed: URL;
  try {
    parsed = new URL(rawUrl);
  } catch {
    return null;
  }

  if (parsed.username || parsed.password || parsed.port) {
    return null;
  }

  const scheme = parsed.protocol.slice(0, -1).toLowerCase();
  const host = parsed.hostname.toLowerCase();

  if (
    scheme === policy.completionScheme.toLowerCase() &&
    host === policy.completionHost.toLowerCase() &&
    parsed.pathname === policy.completionPath &&
    !parsed.search &&
    !parsed.hash
  ) {
    return 'completion';
  }

  if (
    policy.oauthRedirect &&
    scheme === 'https' &&
    host === policy.oauthRedirect.host.toLowerCase() &&
    parsed.pathname === policy.oauthRedirect.path
  ) {
    return 'oauth-return';
  }

  return null;
}

@Injectable({ providedIn: 'root' })
export class PlaidReturnCoordinator {
  private readonly bridge = inject(NATIVE_URL_BRIDGE);
  private listener: PluginListenerHandle | undefined;
  private readonly returnSignalState = signal<PlaidReturnSignal | null>(null);

  readonly returnSignal = this.returnSignalState.asReadonly();

  async start(policy: PlaidReturnPolicy = PLAID_RETURN_POLICY): Promise<void> {
    if (this.listener) {
      return;
    }

    this.listener = await this.bridge.addUrlOpenListener((url) => {
      void this.accept(url, 'resume', policy);
    });

    const launchUrl = await this.bridge.getLaunchUrl();
    if (launchUrl) {
      await this.accept(launchUrl, 'cold-start', policy);
    }
  }

  async stop(): Promise<void> {
    await this.listener?.remove();
    this.listener = undefined;
  }

  private async accept(
    rawUrl: string,
    source: PlaidReturnSource,
    policy: PlaidReturnPolicy,
  ): Promise<void> {
    const kind = classifyPlaidReturnUrl(rawUrl, policy);
    if (!kind) {
      return;
    }

    this.returnSignalState.set({ kind, source });

    if (kind === 'completion') {
      try {
        await this.bridge.closeBrowser();
      } catch {
        // Browser closure is best effort; the callback remains non-authoritative.
      }
    }
  }
}
