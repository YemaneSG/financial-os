import { Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { Capacitor } from '@capacitor/core';

import { PlaidReturnCoordinator } from './core/native/plaid-return';

type AppView = 'home' | 'activity' | 'reflect';
type ActivityFilter = 'all' | 'food' | 'shopping' | 'bills';
type ReflectionChoiceTone = 'positive' | 'neutral' | 'negative';

interface ActivityItem {
  readonly id: string;
  readonly merchant: string;
  readonly detail: string;
  readonly date: string;
  readonly amount: string;
  readonly category: Exclude<ActivityFilter, 'all'>;
  readonly glyph: string;
  readonly pending?: boolean;
  readonly receipt?: boolean;
}

interface ReflectionChoice {
  readonly id: string;
  readonly label: string;
  readonly shortLabel: string;
  readonly tone: ReflectionChoiceTone;
}

interface ReflectionItem {
  readonly id: string;
  readonly merchant: string;
  readonly item: string;
  readonly context: string;
  readonly amount: string;
  readonly date: string;
  readonly question: string;
  readonly prompt: string;
  readonly choices: readonly [ReflectionChoice, ReflectionChoice, ReflectionChoice];
  readonly accent: string;
}

interface ReflectionAnswer {
  readonly item: ReflectionItem;
  readonly choice: ReflectionChoice | null;
}

const ACTIVITY: readonly ActivityItem[] = [
  {
    id: 'activity-1',
    merchant: 'Costco',
    detail: 'Groceries & household',
    date: 'Today',
    amount: '$126.48',
    category: 'shopping',
    glyph: 'C',
    receipt: true,
  },
  {
    id: 'activity-2',
    merchant: 'H-E-B',
    detail: 'Groceries',
    date: 'Yesterday',
    amount: '$54.21',
    category: 'food',
    glyph: 'H',
    receipt: true,
  },
  {
    id: 'activity-3',
    merchant: 'CenterPoint Energy',
    detail: 'Utilities',
    date: 'Aug 14',
    amount: '$87.16',
    category: 'bills',
    glyph: 'E',
  },
  {
    id: 'activity-4',
    merchant: 'Local Coffee',
    detail: 'Dining',
    date: 'Aug 13',
    amount: '$6.75',
    category: 'food',
    glyph: 'L',
    pending: true,
  },
  {
    id: 'activity-5',
    merchant: 'Target',
    detail: 'Shopping',
    date: 'Aug 12',
    amount: '$42.38',
    category: 'shopping',
    glyph: 'T',
  },
];

const REFLECTIONS: readonly ReflectionItem[] = [
  {
    id: 'reflection-1',
    merchant: 'Costco',
    item: 'Portable label maker',
    context: 'Added during the weekly grocery trip',
    amount: '$39.99',
    date: 'Purchased 8 days ago',
    question: 'Is this purchase serving you?',
    prompt: 'Think about whether it has earned a place in your routine.',
    accent: '#f0a45d',
    choices: [
      { id: 'not-serving', label: 'Not really', shortLabel: 'Not really', tone: 'negative' },
      { id: 'unsure', label: 'Not sure yet', shortLabel: 'Unsure', tone: 'neutral' },
      { id: 'serving', label: 'Serving me', shortLabel: 'Serving me', tone: 'positive' },
    ],
  },
  {
    id: 'reflection-2',
    merchant: 'Costco',
    item: 'Protein shakes · 18 pack',
    context: 'Repeat purchase · bought 4 times',
    amount: '$31.99',
    date: 'Purchased 8 days ago',
    question: 'Would you buy this again?',
    prompt: 'Your answer helps separate useful repeats from automatic ones.',
    accent: '#6d9f7d',
    choices: [
      { id: 'would-not-buy', label: 'Would not', shortLabel: 'Would not', tone: 'negative' },
      { id: 'unsure', label: 'Not sure', shortLabel: 'Unsure', tone: 'neutral' },
      { id: 'would-buy', label: 'Absolutely', shortLabel: 'Buy again', tone: 'positive' },
    ],
  },
  {
    id: 'reflection-3',
    merchant: 'Local Coffee',
    item: 'Afternoon coffee',
    context: 'Different from your usual weekday pattern',
    amount: '$6.75',
    date: 'Purchased 3 days ago',
    question: 'How planned was this?',
    prompt: 'There is no wrong answer. This is context, not a judgment.',
    accent: '#6d88b3',
    choices: [
      { id: 'in-the-moment', label: 'In the moment', shortLabel: 'In the moment', tone: 'negative' },
      { id: 'unsure', label: 'Hard to say', shortLabel: 'Unsure', tone: 'neutral' },
      { id: 'planned', label: 'Planned', shortLabel: 'Planned', tone: 'positive' },
    ],
  },
];

@Component({
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit, OnDestroy {
  private readonly plaidReturnCoordinator = inject(PlaidReturnCoordinator);
  private touchStartX: number | null = null;

  readonly plaidReturn = this.plaidReturnCoordinator.returnSignal;
  readonly plaidReturnListener = this.plaidReturnCoordinator.listenerState;
  readonly plaidReturnDisposition = this.plaidReturnCoordinator.disposition;

  readonly currentView = signal<AppView>('home');
  readonly activityFilter = signal<ActivityFilter>('all');
  readonly activitySearch = signal('');
  readonly reflectionIndex = signal(0);
  readonly reflectionHistory = signal<readonly ReflectionAnswer[]>([]);
  readonly toast = signal<string | null>(null);

  readonly recentActivity = ACTIVITY.slice(0, 3);
  readonly reflectionTotal = REFLECTIONS.length;
  readonly filteredActivity = computed(() => {
    const filter = this.activityFilter();
    const query = this.activitySearch().trim().toLowerCase();

    return ACTIVITY.filter((item) => {
      const matchesFilter = filter === 'all' || item.category === filter;
      const matchesQuery =
        !query ||
        item.merchant.toLowerCase().includes(query) ||
        item.detail.toLowerCase().includes(query);
      return matchesFilter && matchesQuery;
    });
  });
  readonly currentReflection = computed(() => REFLECTIONS[this.reflectionIndex()] ?? null);
  readonly reflectionProgress = computed(() =>
    Math.round((this.reflectionIndex() / this.reflectionTotal) * 100),
  );
  readonly completedReflections = computed(
    () => this.reflectionHistory().filter((entry) => entry.choice !== null).length,
  );

  ngOnInit(): void {
    if (Capacitor.isNativePlatform()) {
      void this.plaidReturnCoordinator.start().catch(() => undefined);
    }
  }

  ngOnDestroy(): void {
    void this.plaidReturnCoordinator.stop().catch(() => undefined);
  }

  setView(view: AppView): void {
    this.currentView.set(view);
    this.toast.set(null);
  }

  setActivityFilter(filter: ActivityFilter): void {
    this.activityFilter.set(filter);
  }

  setActivitySearch(event: Event): void {
    this.activitySearch.set((event.target as HTMLInputElement).value);
  }

  answerReflection(choice: ReflectionChoice): void {
    const item = this.currentReflection();
    if (!item) return;

    this.reflectionHistory.update((history) => [...history, { item, choice }]);
    this.reflectionIndex.update((index) => index + 1);
    this.toast.set(`Saved: ${choice.shortLabel}`);
  }

  skipReflection(): void {
    const item = this.currentReflection();
    if (!item) return;

    this.reflectionHistory.update((history) => [...history, { item, choice: null }]);
    this.reflectionIndex.update((index) => index + 1);
    this.toast.set('Skipped — no label was recorded');
  }

  undoReflection(): void {
    const history = this.reflectionHistory();
    if (history.length === 0) return;

    this.reflectionHistory.set(history.slice(0, -1));
    this.reflectionIndex.update((index) => Math.max(0, index - 1));
    this.toast.set('Last answer undone');
  }

  restartReflection(): void {
    this.reflectionHistory.set([]);
    this.reflectionIndex.set(0);
    this.toast.set(null);
  }

  onTouchStart(event: TouchEvent): void {
    this.touchStartX = event.changedTouches[0]?.clientX ?? null;
  }

  onTouchEnd(event: TouchEvent): void {
    const item = this.currentReflection();
    const endX = event.changedTouches[0]?.clientX;
    if (!item || this.touchStartX === null || endX === undefined) return;

    const movement = endX - this.touchStartX;
    this.touchStartX = null;
    if (Math.abs(movement) < 72) return;

    this.answerReflection(movement > 0 ? item.choices[2] : item.choices[0]);
  }
}
