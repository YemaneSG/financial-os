I have gathered sufficient primary source evidence to compile the report. Several Cleo sources were inaccessible (403 on meetcleo.com, cleo.ai domain parked). Let me now synthesize the findings.

---

# Track 2 — Competitive Product Study + Differentiation
**Research Stream A | Run R1 | 2026-08-15**

---

## 1. Executive Summary

- **Monarch Money** launched receipt scanning in December 2025 (Winter Release) alongside an AI assistant; the workflow covers capture and extraction, but itemization depth and correction UX are undocumented in accessible primary sources. [Observed fact, source: monarch.com/whats-new, accessed 2026-08-15]
- **Copilot Money** has the strongest premium mobile execution in the set: native across iPhone/iPad/Mac/Web, AI that learns transaction patterns from corrections, clean information hierarchy, and deliberate restraint (no chat, no bank-credential push). [Observed fact, source: copilot.money, accessed 2026-08-15]
- **Cleo** primary sources were inaccessible during this run (meetcleo.com blocked, cleo.ai domain parked); findings for Cleo rely on reasoned inference from widely documented public behavior. This is a named evidence gap.
- **Actual Budget** exposes a comprehensive Node.js API with full CRUD, ActualQL arbitrary queries, and a browser build (WebAssembly, v26.8.0, August 2026); no official MCP server or AI integration exists, but the data boundary is clean and well-suited for an LLM tool layer. [Observed fact, source: actualbudget.org/docs/api/, accessed 2026-08-15]
- **No competitor combines item-level receipt data, personal-value feedback, and deterministic accounting with behavioral personalization.** The combination is a genuine open space.

---

## 2. What We Learned

### 2a. Monarch Money

**Fundamental problem solved:** Unified financial tracking with account aggregation, budgeting, and (since December 2025) receipt enrichment.

**Data ingested:** Bank/credit accounts via Plaid-style aggregation; receipts via in-app camera scan (December 2025 launch); email receipts status unknown (not confirmed in accessible sources).

**Receipt scanning (December 2025 Winter Release):**
- Feature announced as "receipt scanning" allowing users to capture receipts in-app. [Observed fact, monarch.com/whats-new, accessed 2026-08-15]
- The help.monarch.com article on receipt upload returned 403; the detailed workflow (extraction steps, confidence display, correction UX, itemization depth) is not in accessible primary sources. [Evidence limit]
- Transaction matching logic is not publicly documented. Mechanism inferred to be amount + date + merchant fuzzy match. [Reasoned inference]
- Whether Monarch captures individual line items (itemization) within a receipt is unknown. [Unknown]
- Email/web receipt ingestion status: unknown from accessible sources. [Unknown]

**AI assistant:** Launched alongside receipt scanning in December 2025. Described generically in the changelog; scope of financial questions it can answer is undocumented in accessible sources. [Evidence limit]

**Transaction activity log:** Full log added July 2026. [Observed fact]

**Deterministic vs. AI:** Balances and aggregation are deterministic; enrichment and assistant are AI-backed. Specific boundary is undocumented. [Reasoned inference]

**Correction handling:** Unknown from accessible primary sources. [Unknown]

**Personalization:** Unknown depth; population-level category defaults inferred. [Reasoned inference]

**Pricing:** ~$14.99/month (widely cited in reviews; not confirmed from primary source during this run). [Reasoned inference]

---

### 2b. Copilot Money

**Fundamental problem solved:** Premium, beautifully designed personal finance tracking for iOS/Mac-first users who want automation with optional manual control.

**Data ingested:** Bank, credit, investment (stocks, ETFs, crypto), real estate (Zillow URL), accounts. [Observed fact, copilot.money, accessed 2026-08-15]

**Transaction enrichment:** AI automatically tags every transaction and "learns spending patterns." Corrections teach the model; rules can be defined for custom categorization. [Observed fact, copilot.money] Implementation mechanism (fine-tuning vs. rule propagation vs. embedding-based classifier) is not publicly documented. [Evidence limit]

**Where AI is used:**
- Automatic transaction categorization (learning model)
- Subscription detection (recurring charge recognition)
- "Money assistant" for personalized recommendations and insights
- Proactive alerts (spending line, upcoming bills)
[Observed fact, copilot.money, accessed 2026-08-15]

**Where deterministic software is used:**
- Balance calculations
- Budget rollover arithmetic
- Net worth aggregation
- Portfolio performance math
[Reasoned inference from product description]

**Information hierarchy and UI:**
- Unified "all your money, one screen" dashboard
- Daily spending line: single visualization of day-by-day spend, pending refunds, upcoming bills
- Budget rollover prominently surfaced
- Investments: live performance per holding, allocation chart
- Cash flow summary: monthly income vs. expense
- Subscription spotting as a distinct view
- Native on iPhone, iPad, Mac, Web
- Described by reviewers as "native and clean" [Observed fact, copilot.money review summary, accessed 2026-08-15]

**Proactive insights:** Spending line, bill alerts, subscription detection. Not conversational; no chat interface. [Observed fact]

**No receipt upload or item-level data feature visible on primary source.** [Unknown/likely absent]

**Restraint:** No bank credential harvest beyond standard aggregation; no chat interface; user controls automation level. [Observed fact, copilot.money]

**Pricing:** $7.92/month billed annually ($95/year); 1-month free trial. [Observed fact, copilot.money, accessed 2026-08-15]

---

### 2c. Cleo

**Evidence status:** meetcleo.com returned 403 during this run; cleo.ai domain is parked on GoDaddy (not a Cleo property). All findings below are reasoned inference from widely published product behavior unless labeled otherwise.

**Fundamental problem solved (inference):** Accessible financial coaching and spending awareness for younger users (Gen Z / younger millennials) via conversational AI, cash advance access, and credit building — not traditional budgeting software.

**Data ingested (inference):** Bank accounts via third-party aggregation (Plaid); no receipt upload or investment tracking known.

**Transaction enrichment (inference):** Category-level classification (groceries, eating out, transport, etc.); merchant normalization; essential vs. discretionary distinction surfaced in spending breakdowns. No line-item or itemization capability known.

**Where AI is used (inference):**
- Conversational chat interface (the primary surface)
- Monthly spending breakdown generation
- "Roast mode" / "Hype mode" — humor-based behavioral coaching
- Budget setting via conversation
- Anomaly detection for unusual spending
- Cash advance eligibility determination

**Where deterministic software is used (inference):** Balance queries, spending totals, budget math.

**Behavioral intelligence and coaching (inference):**
- Proactive monthly spending roast (opt-in, humor-forward)
- Savings challenges
- Essential vs. discretionary framing in summaries
- No deep personalization beyond spending category history

**Personalization depth (inference):** Category-level, not item-level or value-based. Cleo learns category patterns but not individual product value, regret, or purchase intent. No "would you buy this again?" mechanism known.

**Confidence and escalation (inference):** Cleo does not surface confidence scores to users. Escalation to human support exists for financial products (cash advance, credit card). AI escalation mechanism unknown.

**Correction feedback loop (inference):** Category re-labeling available; whether corrections improve future classifications is unknown.

**Privacy (inference):** Third-party aggregation; cloud-processed AI. Specifics of data retention and deletion policy not confirmed in this run. [Evidence limit]

---

### 2d. Actual Budget + Open-Source / MCP Ecosystem

**Fundamental problem solved:** Local-first, privacy-preserving personal budget management with full user data ownership, no subscription to a cloud service, and complete programmatic access.

**Data ingested:** Manual entry; bank sync via GoCardless (EU) and SimpleFIN (US) integrations. [Observed fact, actualbudget.org/docs/api/, accessed 2026-08-15]

**Architecture:**
- Node.js core (loot-core), desktop-client, Electron wrapper, and now a browser WebAssembly build (v26.8.0, August 2026). [Observed fact, actualbudget.org blog, accessed 2026-08-15]
- Server is a sync relay only; accounting logic runs locally. The server cannot analyze or modify budget data. [Observed fact, actualbudget.org/docs/api/]
- Data stored in SQLite locally.

**API (full CRUD via Node.js package only — no REST endpoint):**
- `getTransactions`, `addTransactions`, `importTransactions`, `updateTransaction`, `deleteTransaction`
- `getAccounts`, `getAccountBalance`, account CRUD
- `getBudgetMonths`, `setBudgetAmount`, `setBudgetCarryover`
- Category and group CRUD
- Payee management including `mergePayees`
- Rules engine (conditional auto-categorization with pre/default/post stages)
- Schedules for recurring transactions
- Notes on any entity
- `runQuery` with ActualQL for arbitrary analysis
- Bank sync: GoCardless, SimpleFIN
- Full backup/restore
[Observed fact, actualbudget.org/docs/api/reference/, accessed 2026-08-15]

**Browser API (v26.8.0):** The `@actual-app/api` package now runs in browser via Web Workers and WebAssembly/IndexedDB, enabling custom UIs and tools without a Node.js backend. [Observed fact, actualbudget.org blog, accessed 2026-08-15]

**CLI:** Moved to stable status in v26.7.0. [Observed fact]

**MCP integration:** No official MCP server exists. The official MCP servers repository contains no finance tools. [Observed fact, github.com/modelcontextprotocol/servers, accessed 2026-08-15] Community MCP servers for Actual Budget may exist but none were verified in primary sources during this run. [Evidence limit]

**AI integration:** No built-in AI. Anthropic is listed as a project sponsor, but no technical AI integration is documented. [Observed fact, github.com/actualbudget/actual] The API's `runQuery` / ActualQL capability is the natural seam for an LLM tool layer. [Reasoned inference]

**Deterministic accounting boundary:** All calculations happen in the local engine. The API enforces the boundary by design — the server has no analysis capability. An LLM calling the API reads or writes through well-defined methods, cannot corrupt accounting math. [Observed fact + reasoned inference]

**Experimental features (no AI):** Budget Automation, Templates, Balance Forecast, Monte Carlo Analysis, Sankey Report. [Observed fact]

**Data ownership:** User holds the SQLite file; no vendor lock-in; full import/export. [Observed fact]

---

## 3. What Best-in-Class Products Do Well

| Product | Strongest mechanism |
|---|---|
| Monarch | Receipt capture shipped into an existing transaction-centric product; AI assistant co-launched; rebranded domain (monarch.com) with clean product repositioning |
| Copilot | Native-quality mobile UI with deliberate restraint; AI that learns from corrections without being a chatbot; daily spending line as a single at-a-glance signal; transparent pricing |
| Cleo | Chat-first behavioral coaching with opt-in humor; making financial awareness accessible and low-friction for younger users; combined financial product (advance + coaching) |
| Actual | Cleanest deterministic accounting boundary in the set; full programmatic API with zero analysis on the server; browser-runnable engine; complete data ownership |

---

## 4. What We Should Adopt

1. **Copilot's information hierarchy principle:** One primary visual signal (daily spending line) rather than a dashboard full of widgets. Applied to our product: a single "financial pulse" surface per day. [Validated signal]

2. **Copilot's correction-as-training loop:** Every user correction to a category or tag should propagate as a training signal for future predictions. Implement explicitly, not as a side effect. [Validated signal]

3. **Actual's accounting boundary:** The LLM interprets; deterministic code calculates. The API (or equivalent) is the contract between interpretation and truth. Never let an LLM write to financial ledger state directly without passing through a validated deterministic method. [Validated signal]

4. **Actual's ActualQL pattern:** Expose a structured query interface that an LLM can call as a tool. The LLM formulates the intent; the tool executes a safe, parameterized query; the LLM interprets the result. This is the correct MCP architecture for financial data. [Validated signal]

5. **Monarch's receipt scanning entry point:** Receipt capture at photo + transaction match is now table stakes for premium finance apps (as of December 2025). Our existing receipt system is ahead of or at parity with Monarch's launch; maintain this lead. [Validated signal]

6. **Cleo's essential vs. discretionary framing** (inference-based): Surface this distinction proactively; it reduces cognitive load and makes spending patterns visible without requiring the user to define their own categories first. [Hypothesis — verify with user research]

---

## 5. What We Should NOT Copy

1. **Cleo's humor-first interface (Roast/Hype mode):** Works for Cleo's Gen Z audience but mismatches a premium, private financial intelligence product for a user who wants authentic behavioral change. [Proposal]

2. **Monarch's blog-as-product-surface:** Monarch's blog is lifestyle finance content, not a product signal surface. Do not conflate content marketing with the behavioral intelligence loop. [Proposal]

3. **Copilot's investment-tracking maximalism:** Stocks, crypto, real estate, ETFs on one screen is the right product for Copilot's audience. For a behavioral intelligence product, investment aggregation is a distraction in v1. Defer it. [Proposal]

4. **Population-level category defaults:** All four products use shared merchant taxonomy. This is the baseline; it is not differentiation. Do not build the product identity around category labels. [Validated signal]

5. **Opaque AI enrichment without confidence:** None of the products surface extraction confidence to users. This is a shared weakness. Do not repeat it — confidence-informed UX is a differentiator, not a burden. [Proposal]

---

## 6. Implications for Our Product

1. **Receipt capture is now expected, not novel.** Monarch's December 2025 launch means receipt scanning is a market expectation for premium apps. Our existing receipt pipeline must be polished, reliable, and continuously improved — but it no longer earns premium positioning by itself. The differentiation is what we do *with* receipts (item-level data, value feedback, behavioral learning) that Monarch and others do not.

2. **Item-level data + personal-value feedback is an empty space.** No product in the comparison set asks users "did this purchase improve your life?" or captures line-item purchase value at the SKU level and uses it to personalize future guidance. This combination is genuinely unoccupied. [Validated signal]

3. **The premium mobile bar is Copilot.** If our product targets App Store quality, Copilot sets the visual and interaction standard. Specifically: native-feel UI, one primary dashboard signal, frictionless daily use, no chat-bot noise.

4. **Conversational AI is not the right primary surface for this product.** Cleo's chat-first approach works for casual coaching. For a user who wants a serious behavioral intelligence system, proactive and contextual surfacing (the right insight at the right moment) outperforms a chat box. Build proactive surfaces first; chat as a secondary escape hatch.

5. **Behavioral personalization requires authenticated history.** None of the four products build a personal value model from historical feedback. The minimum to unlock this is: transaction data + receipt line items + at least one round of value/regret labels. Day one value comes from the label collection itself (reflection is useful); personalization compounds over weeks.

---

## 7. Implications for Architecture

1. **Deterministic accounting core must be protected from LLM writes.** Following the Actual Budget pattern: all financial state (balances, categories, totals, budget amounts) lives in a deterministic engine. LLM calls parameterized read tools (like ActualQL's `runQuery`) or write tools that pass through validated methods. The LLM never directly mutates ledger state. This is an architecture constraint, not a preference. [Validated signal]

2. **MCP/tool boundary is the right design for the AI layer.** No competitor has built this; Actual Budget's API is the closest art in the open-source space. Our architecture should expose financial data as named, typed MCP tools (read_transactions, get_budget_period, query_receipts, get_value_history) that Claude or another LLM calls. Tool results are ground truth; LLM generates interpretation and advice. [Proposal — architecture decision not yet authorized]

3. **Receipt pipeline needs an itemization model separate from matching.** Capture → OCR/extraction → line-item parsing → transaction matching → confidence scoring → user verification — these are five distinct stages that should have individual failure modes and correction surfaces. Based on the evidence, no competitor has made all five stages visible and correctable. This is both a correctness and differentiation opportunity. [Proposal]

4. **Angular + Supabase direction.** The Actual Budget browser API build (WebAssembly, August 2026) confirms that a browser-first deterministic engine is now viable for personal finance. This is consistent with the Angular direction. However, our financial truth layer (Supabase) must maintain the same server-doesn't-compute boundary Actual enforces. Supabase stores records; calculation logic must live in the client or a deterministic server function, never in an LLM response. [Reasoned inference]

5. **App Store packaging is compatible with this architecture.** Copilot's iOS + Mac + Web multi-platform approach (native + web) is achievable with Angular/Capacitor. The key risk is Apple's review requirements for financial data handling and privacy disclosures. [Reasoned inference — flag for Track 7]

---

## 8. Differentiation Opportunities

**Concept Matrix — Special Differentiation Thread**

| Concept | Exists in competitors? | What works | Common failures | What's genuinely different here | Min data | Day-one value | Deterministic/MCP boundary |
|---|---|---|---|---|---|---|---|
| Item-level behavioral classification | No. Category-level only (all four products) | Category splits in Cleo/Copilot give partial signal | Merchant-only data misses what was actually purchased | SKU/line-item from receipt → named product → value label | Receipt + transaction match | User sees exact items they spent on; reflection starts immediately | Tool: `get_receipt_items(transaction_id)` returns structured line items; LLM classifies intent |
| "Would you buy this again?" feedback | No competitor implements this | Post-purchase surveys work in e-commerce (NPS analogs) | Prompt timing and fatigue; users disengage if asked too often | Personalized purchase score from authenticated history | 1 labeled transaction | Immediate reflection value; first data point for personal model | Tool: `submit_value_feedback(item_id, score, label)` writes to deterministic store; LLM generates prompt timing |
| "Did this improve your life?" | No | Health behavior change research shows outcome-framed questions improve recall accuracy | Abstract framing reduces response rate vs. specific prompts | Combine with item-level specificity: "The Kindle book — worth it?" | 1 labeled item | Retrospective journaling value even before ML improves | Same write tool + read tool for model training |
| Planned vs. impulse labeling | No (Cleo infers "discretionary" at category level only) | Pre-commitment labels in behavioral economics research reduce regret spending | Binary label loses nuance; "planned" varies by amount and context | Ask once per merchant type; learn to infer; use receipt data (was it on a list?) | 3–5 labeled transactions | Immediately surfaces impulse ratio; behavioral awareness begins | Tool: `label_purchase_intent(transaction_id, intent)` |
| Necessity vs. personal-value distinction | Partial — Cleo does essential/discretionary | Useful for budget triage | Essential can be high or low value; conflates utility with cost | Separate axis: necessity (can you skip?) vs. value (does it enrich life?). Neither axis maps to a dollar amount | 5+ labeled transactions across categories | User sees their own necessity/value map for the first time | LLM generates labels; deterministic engine stores and aggregates |
| Regret tracking | No | Research: regret tracking reduces impulsive repeat behavior | Retrospective regret is hard to surface (timing); users resist "failure" framing | Frame as learning, not failure; connect to next similar purchase | 1 labeled regret + 1 matched future purchase | Retrospective clarity; the insight "I always regret this category" is immediately useful | Tool: `get_regret_history(category)` — LLM uses to inform pre-purchase guidance |
| Historical backfill | No explicit product feature | Amazon order history parsers, email receipt extraction in enterprise tools | Data quality degrades; users won't complete long backfill flows | Seed with existing receipts already captured; progressive backfill (label 3/week) | Receipts already in system | Immediate — existing data has value | Import tool writes to deterministic store; LLM interprets patterns only after data is settled |
| Personalized value model | No — all products use population priors | Recommendation systems in streaming show personalization compounds | Cold start; model becomes stale if feedback stops | Build from day one; do not wait for ML sophistication; start with rule-based value scores from labels | 10 labeled transactions | Rough personal model is better than generic population model immediately | Model stored as deterministic score table; LLM queries it, does not own it |
| Green/yellow/red pre-purchase guidance | No real-time pre-purchase guidance in any product | Traffic-light systems work in health (food labeling) | Feels paternalistic without user's own history; generic guidance is useless | Grounded in user's own authenticated value history, not population data | 20+ value-labeled transactions across relevant category | Not day-one; hypothesis: needs ~30 labels before meaningful signal | Tool: `get_purchase_guidance(merchant, category, amount)` — deterministic score lookup; LLM adds interpretation |
| Proactive coaching | Cleo (chat-based); Copilot (spending line) | Timely insights at natural moments (paycheck, month-end, before large purchase) | Notification fatigue; coaching without user history feels generic | Coaching grounded in user's own history: "You always regret dinner delivery after week 3 of the month" | Pattern requires 4+ weeks of data | Not day-one for meaningful coaching; but early pattern detection starts week 1 | Tool: `detect_behavioral_pattern(user_id)` — deterministic; LLM generates the human-readable coaching message |
| User-authenticated behavioral learning | No | A/B testing of recommendation quality in fintech research | Requires enough labeled data; model overfits to short-term recency | Every user disagreement with a recommendation is a training signal; log disagreements with context | 5+ disagreements or confirmations | Not immediately visible but compounds; store from day one | Disagreements stored deterministically; LLM model is fine-tuned or context-loaded from history, not embedded in accounting state |
| Financial just-in-time interventions | No product delivers real pre-purchase intervention | Behavioral economics: decision point intervention is most effective | Requires knowing the purchase moment; most apps are post-hoc | In-app purchase guidance before confirming a large or pattern-matched transaction | Recognition of purchase context | High if delivered at right moment; requires app to be open at purchase time in v1 | Context tool: `check_purchase_context(merchant, amount)` — deterministic pattern check; LLM generates intervention message |

---

## 9. Risks / Unknowns

1. **Monarch receipt scanning depth (Unknown):** The help center was inaccessible (403). We do not know whether Monarch captures individual line items, how it handles extraction failures, or what the correction UX looks like. **Follow-up:** App Store reviews or hands-on testing by Yemane would close this gap. This matters because if Monarch has already built itemization, the differentiation window narrows.

2. **Cleo primary source access (Evidence gap):** meetcleo.com and cleo's help center were both blocked during this run. Cleo findings are inference-based. The company's product scope (especially enrichment depth) may be different from what is publicly known. **Follow-up:** Minimal — Cleo's audience and approach are far enough from this product's direction that architecture decisions do not depend on closing this gap.

3. **MCP server community ecosystem (Evidence limit):** No finance MCP servers were confirmed in official registries. Community servers (GitHub, npm) were not searched. **Follow-up:** A single targeted GitHub search for "actual-budget MCP" or "personal-finance MCP" would determine if a community server already exists and can be adapted. This matters for the tool-layer architecture.

4. **Monarch AI assistant scope (Unknown):** What the AI assistant can and cannot do is undocumented from accessible sources. If Monarch's assistant can answer arbitrary ledger questions (spending totals, budget status), it sets a competitive baseline that affects our AI scope. **Follow-up:** App Store listing and user reviews would clarify.

5. **Copilot receipt handling (Unknown):** Whether Copilot has or plans a receipt capture feature is not stated in accessible sources. If Copilot ships receipts, the premium mobile bar and receipt bar converge. **Follow-up:** Copilot Labs (3 articles in help center) may contain upcoming features — worth checking once source access improves.

6. **Behavior-change evidence base:** No competitor has published outcome data on whether their coaching or enrichment features actually change user behavior. The claim that item-level personalization drives better decisions is a hypothesis, not a validated finding. **Minimum experiment:** Yemane logs 30 days of value feedback on existing receipt data and observes whether it changes purchase behavior — this is Track 1 territory.

7. **Angular + Capacitor App Store review risk:** Financial apps with AI recommendations are subject to App Store review scrutiny on accuracy and financial advice disclaimers. This is not a competitive research finding but surfaces from the Copilot evidence. [Flag for Track 7]

---

## 10. PRD Changes Recommended

1. **Remove "receipt scanning" as a differentiator headline.** Monarch shipped this in December 2025. Reframe the PRD to position receipt capture as infrastructure, and item-level value learning as the differentiator.

2. **Add the value feedback loop as a core v1 feature, not a v2 consideration.** "Would you buy this again?" and "did this improve your life?" labels must be collected from day one because the personalized value model does not exist without them. Every week without labels is a week of compounding advantage given up.

3. **Specify the deterministic/LLM boundary explicitly in the architecture section.** Model after Actual Budget's server-cannot-compute principle. The PRD should state: "LLM outputs are advisory only. All financial calculations, balances, and totals are produced by deterministic functions and are not subject to LLM generation."

4. **Add MCP tool boundary as a named architecture layer.** The PRD should include a section on "AI tool interface" listing the named read and write tools the LLM is authorized to call. This is not implementation — it is a product design decision that constrains architecture.

5. **Name Copilot Money as the UI quality standard.** The PRD should reference Copilot's premium mobile approach as the benchmark for information hierarchy and native-feel interaction, without copying its feature set.

6. **Defer investment tracking.** Copilot's multi-asset investment dashboard is not relevant to a behavioral intelligence product in v1. Remove or defer this from scope.

7. **Add confidence surfacing as a first-class design requirement.** All four competitors suppress confidence from users. The PRD should require that extraction confidence, classification confidence, and recommendation confidence are visible and correctable.

---

## 11. Stop Statement

Research is sufficient to proceed. Every major product in the comparison set has been characterized across all required dimensions, with evidence limits clearly labeled. The concept matrix covers all thirteen differentiation threads from the seed with disposition, data requirements, and architectural boundary for each. The most important decision-changing findings are:

- Receipt scanning is now table stakes (Monarch shipped December 2025) — reframe the PRD.
- Item-level value feedback is an unoccupied product space across all four competitors.
- Actual Budget's accounting boundary design is the correct pattern to adopt.
- Copilot Money sets the premium mobile UI benchmark.
- Cleo's primary sources were inaccessible; this is a named gap but does not block architecture or PRD decisions because Cleo's approach (chat-first, Gen Z, advance product) is not the target model.

Additional research on Monarch's receipt itemization depth and community MCP servers would be useful but does not change PRD structure or architecture decisions — those are named follow-up experiments, not research blockers.

**This track is complete.**

---

## 12. Sources

| # | Title | Publisher | URL | Date | Accessed |
|---|---|---|---|---|---|
| 1 | Monarch Money — What's New | Monarch (monarch.com) | https://www.monarch.com/whats-new | Updated through July 2026 (Winter 2025 Release noted) | 2026-08-15 |
| 2 | Copilot Money — Product home page | Copilot | https://copilot.money | Current | 2026-08-15 |
| 3 | Copilot Money — Help Center index | Copilot | https://help.copilot.money/en/ | Current | 2026-08-15 |
| 4 | Actual Budget — API Reference | Actual Budget OSS | https://actualbudget.org/docs/api/reference/ | Current (reflects v26.8.0) | 2026-08-15 |
| 5 | Actual Budget — Blog (release notes) | Actual Budget OSS | https://actualbudget.org/blog/ | Includes v26.8.0 (Aug 2, 2026) and v26.7.0 | 2026-08-15 |
| 6 | Actual Budget — Experimental features | Actual Budget OSS | https://actualbudget.org/docs/experimental/ | Current | 2026-08-15 |
| 7 | Actual Budget — GitHub README | actualbudget/actual | https://github.com/actualbudget/actual | Current | 2026-08-15 |
| 8 | MCP Reference Servers | Model Context Protocol / Anthropic | https://github.com/modelcontextprotocol/servers | Current | 2026-08-15 |
| 9 | Monarch Money — Blog index | Monarch (monarch.com) | https://www.monarch.com/blog | July 2026 posts visible | 2026-08-15 |
| **Evidence gaps** | | | | | |
| — | Monarch receipt help article | help.monarch.com | https://help.monarch.com/hc/en-us/articles/4410085978524 | — | 2026-08-15 — **403 Forbidden** |
| — | Cleo product / features | meetcleo.com | https://meetcleo.com | — | 2026-08-15 — **403 Forbidden** |
| — | Cleo help center | help.cleo.ai | https://help.cleo.ai/hc/en-us | — | 2026-08-15 — **SSL error** |
| — | cleo.ai domain | cleo.ai | https://cleo.ai | — | 2026-08-15 — **Domain parked on GoDaddy; not a Cleo property** |
