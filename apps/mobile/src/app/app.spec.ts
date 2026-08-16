import { TestBed } from '@angular/core/testing';

import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
    }).compileComponents();
  });

  it('renders the premium home experience with a synthetic-data boundary', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;

    expect(compiled.querySelector('h1')?.textContent).toContain('A calmer look at your money');
    expect(compiled.textContent).toContain('Preview data');
    expect(compiled.textContent).toContain('3 purchases are ready');
  });

  it('navigates to activity and filters transactions', async () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;

    app.setView('activity');
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent).toContain('Activity');
    expect(app.filteredActivity()).toHaveLength(5);

    app.setActivityFilter('bills');
    fixture.detectChanges();
    expect(app.filteredActivity()).toHaveLength(1);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('CenterPoint Energy');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('No bank account is connected');
  });

  it('records, skips, and undoes reflection evidence without treating skip as a label', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;

    app.setView('reflect');
    const firstChoice = app.currentReflection()?.choices[2];
    expect(firstChoice).toBeDefined();
    app.answerReflection(firstChoice!);
    expect(app.reflectionIndex()).toBe(1);
    expect(app.completedReflections()).toBe(1);

    app.skipReflection();
    expect(app.reflectionIndex()).toBe(2);
    expect(app.completedReflections()).toBe(1);

    app.undoReflection();
    expect(app.reflectionIndex()).toBe(1);
    expect(app.reflectionHistory()).toHaveLength(1);
    expect(app.toast()).toBe('Last answer undone');
  });

  it('completes and restarts a three-card reflection session', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;

    for (let index = 0; index < app.reflectionTotal; index += 1) {
      const choice = app.currentReflection()?.choices[1];
      expect(choice).toBeDefined();
      app.answerReflection(choice!);
    }

    expect(app.currentReflection()).toBeNull();
    expect(app.completedReflections()).toBe(3);

    app.restartReflection();
    expect(app.reflectionIndex()).toBe(0);
    expect(app.reflectionHistory()).toHaveLength(0);
  });
});
