import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { Capacitor } from '@capacitor/core';

import { PlaidReturnCoordinator } from './core/native/plaid-return';

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit, OnDestroy {
  private readonly plaidReturnCoordinator = inject(PlaidReturnCoordinator);
  readonly plaidReturn = this.plaidReturnCoordinator.returnSignal;
  readonly plaidReturnListener = this.plaidReturnCoordinator.listenerState;
  readonly plaidReturnDisposition = this.plaidReturnCoordinator.disposition;

  ngOnInit(): void {
    if (Capacitor.isNativePlatform()) {
      void this.plaidReturnCoordinator.start().catch(() => undefined);
    }
  }

  ngOnDestroy(): void {
    void this.plaidReturnCoordinator.stop().catch(() => undefined);
  }
}
