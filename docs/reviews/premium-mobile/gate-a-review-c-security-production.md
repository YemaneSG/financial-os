# Premium Mobile Gate A — Security, Production, and Reliability Review

**Reviewer:** Independent Codex security/reliability subagent
**Mode:** Read-only; no other reviewer output accessed
**Revision 1 verdict:** Reject
**Revision 2 verdict:** **Approve with conditions**

## Independent summary

PM-0A/PM-0B is a synthetic proof of exact Firebase-to-Supabase owner
authorization and safe Plaid Hosted Link return. It processes no real financial
data, persistent Plaid Item, receipt evidence, or production resource. The
receipt collector remains untouched.

## Revision 1 blockers/high findings and disposition

| Finding | Revision 2 disposition |
|---|---|
| Current host cannot meet native evidence | Resolved by PM-0A/PM-0B split; cloud compile alone cannot replace real-iPhone callback proof |
| Owner predicate incomplete across Edge Functions | Resolved by one exact predicate enforced before administrative access |
| Hosted Link return correlation incomplete | Resolved by subject-bound, short-lived, single-use server session and callback non-authority |
| Firebase claim mutation/rollback unspecified | Resolved with synthetic subject, private prior state, read-modify-write, and rollback |
| Plaid token lifecycle ambiguous | Resolved: PM-0 stops before exchange and creates no persistent Item/access token |
| Supply-chain controls not executable | Resolved by frozen lockfile, supported-major pins, credential-free PR CI, minimal permissions, and bounded artifacts |
| Development resource lifecycle/cost absent | Resolved by owner/region/purpose/billing/retention record before creation |
| Callback privacy evidence absent | Resolved by console/crash/navigation/cache/screenshot/bundle/CI inspection |

## Remaining conditions

1. Owner approval and Sandbox permissions precede every resource, identity, secret,
   or dependency change.
2. Plaid/Supabase/Firebase credentials flow only through private channels.
3. PM-0A may start independently, but PM-0 completion requires PM-0B current native
   and device evidence.
4. No live data, production resource, persistent Plaid Item, or receipt-system
   change is authorized.

## Explicit non-findings

- Synthetic PM-0 data does not require a production backup program.
- Vault, verified production webhook, transaction sync, live backup/restore,
  deletion, and export are correctly deferred to packets that trigger them.
- Redis, queues, gateways, and microservices are unnecessary.

**Verdict: Approve with conditions**
