# PM-1A Synthetic Experience Evidence — August 16, 2026

## Result

The Angular/Capacitor application now presents a usable synthetic Home, Activity,
and Reflect experience. The PM-0 native callback coordinator remains present but
is no longer the product's visible landing page.

## User-visible evidence

- **Home:** calm monthly pulse, preview-data disclosure, reflection queue entry,
  and recent activity.
- **Activity:** five deterministic synthetic transactions, search, four category
  filters, sync-state preview, receipt badges, and explicit no-bank boundary.
- **Reflect:** three one-question cards covering personal value, repurchase intent,
  and plannedness; touch swipe, labeled alternatives, skip, progress, completion,
  and undo.
- Browser verification passed at a 390 × 844 viewport for all three screens.
- Save advanced the reflection from 0/3 to 1/3 and displayed Undo; Undo restored
  0/3 and the original card.

## Automated evidence

| Check | Result |
|---|---|
| Mobile lint | Pass |
| TypeScript type check | Pass |
| Angular unit tests | 19/19 pass |
| Angular production build | Pass; 249.07 kB initial raw bundle |
| Premium generated-bundle credential scan | Pass |
| Repository private-data scan | Pass |
| Git whitespace check | Pass |

## Boundaries

- All displayed financial content is synthetic and marked as preview data.
- No bank account is connected by this slice.
- No label is persisted beyond the in-memory preview session.
- No receipt-service file, contract, migration, or production resource is changed.
- PM-0B remains incomplete and separately tracked in issue #16.
