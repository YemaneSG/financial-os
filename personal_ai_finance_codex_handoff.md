# Personal AI Finance Assistant — Codex Handoff

**Project status:** Pre-implementation / V1 definition  
**Primary user:** Yem  
**Purpose of this document:** Give Codex or another coding LLM enough context to begin implementation without needing to reconstruct the product decisions from prior conversations.

---

## 1. Executive Summary

Build a **personal AI finance assistant** whose first job is to capture **every dollar spent at line-item level**.

The core idea is inspired by calorie tracking:

> Instead of only knowing “I spent $120 at H-E-B,” the system should know that the purchase included rice for $10, onions for $6, coffee for $8, etc.

Traditional budgeting apps mostly operate at the **transaction / merchant level**. This project should operate at the **item level** wherever possible.

The system should eventually become a conversational financial copilot that can answer questions such as:

- How much did I spend on coffee this month?
- How much have groceries increased over the last three months?
- What did I spend on fresh vegetables this week?
- Which purchases did not align with my stated priorities?
- How much have I spent on hiking equipment this year?
- Which products am I buying more frequently?
- What purchases do I tend to regret?
- Am I on track with my savings goals?
- Can I afford a discretionary purchase without affecting higher-priority goals?

However, **V1 should stay deliberately small**.

The immediate goal is:

> **Capture first. Analyze second.**

The system should make it extremely easy to capture receipts and spending from an iPhone, then progressively add extraction, normalization, storage, review, analysis, and conversational AI.

---

# 2. Product Philosophy

## 2.1 The calorie-tracking analogy

The product philosophy is similar to detailed food tracking.

A calorie tracker does not merely record:

> Lunch: 800 calories

It records:

- 200 g chicken
- 150 g rice
- olive oil
- vegetables
- sauce
- etc.

This finance system should behave similarly.

A normal banking feed might contain:

```text
Merchant: H-E-B
Amount: $121.42
Category: Groceries
```

The desired financial record is closer to:

```text
Merchant: H-E-B
Receipt total: $121.42

Items:
- Brown rice — $9.98
- Yellow onions — $5.47
- Bananas — $3.22
- Greek yogurt — $6.99
- Coffee — $13.49
- Protein powder — $32.99
...
```

This creates a much richer dataset for future reasoning.

---

# 3. Guiding Principles

## 3.1 Capture first, analyze second

Do not block expense capture because downstream analytics are incomplete.

Yem should be able to begin collecting useful data immediately.

The capture workflow should be usable even while the backend is still evolving.

---

## 3.2 Reduce friction aggressively

The capture experience should be close to:

```text
Open app
→ tap camera
→ photograph receipt
→ submit
→ done
```

Target interaction time should be roughly **10 seconds or less** whenever possible.

The mobile client should initially be intentionally simple.

---

## 3.3 Preserve raw evidence until extraction is trusted

Receipt images do not need to be stored forever.

Recommended lifecycle:

```text
Capture image
→ upload
→ extract
→ parse
→ verify
→ mark confirmed
→ retain temporarily
→ archive or delete according to retention policy
```

Do **not** delete the image immediately after OCR.

Keep it long enough to:

- debug extraction errors,
- compare parser changes,
- manually correct failures,
- recover from malformed structured output.

A reasonable initial retention period might be 30 days, but this should be configurable.

---

## 3.4 Structured data is the long-term source of truth

Receipt images are evidence.

The permanent useful asset is structured financial data.

Long-term records should emphasize:

- transaction,
- merchant,
- receipt,
- line item,
- product,
- quantity,
- unit price,
- total price,
- category,
- timestamp,
- confidence,
- provenance,
- corrections.

---

## 3.5 Separate capture from intelligence

The phone application should not need to know how OCR, parsing, categorization, or AI reasoning works.

Architecturally:

```text
Capture Client
      |
      v
Stable Upload API
      |
      v
Processing Pipeline
      |
      v
Financial Data Store
      |
      v
Analytics / AI
```

This allows components to evolve independently.

---

## 3.6 Build a personal financial memory, not merely a budgeting dashboard

The deeper goal is not simply:

> “How much did I spend?”

It is:

> “What does my spending history reveal about my priorities, habits, goals, and decisions?”

This distinction should guide future architectural decisions.

---

# 4. V1 Product Scope

V1 should focus on five core capabilities.

## Capability 1 — Receipt capture

From an iPhone, Yem can:

1. Open the app.
2. Take a photo of a receipt.
3. Submit it.
4. Receive a simple success acknowledgement.

The app should not require categorization or editing at capture time.

---

## Capability 2 — Receipt extraction

The backend should extract:

### Receipt-level information

- merchant name
- merchant location if available
- transaction date
- transaction time if available
- subtotal
- taxes
- discounts
- tips if applicable
- total
- payment method if visible

### Line-item information

- raw item description
- quantity
- unit price
- extended price
- discounts
- inferred category
- confidence

---

## Capability 3 — Structured storage

Store extracted information in a queryable database.

Initial database can be SQLite.

The schema should be designed so migration to PostgreSQL later is straightforward.

---

## Capability 4 — Human verification

AI extraction will sometimes be wrong.

Low-confidence records should enter a review queue.

The system should make correction fast.

Example:

```text
AI extracted:

"ORG BNNA 2.18"

Possible interpretation:
Organic Bananas — $2.18

Confirm?
[Yes] [Edit]
```

Corrections should be preserved so normalization and extraction can improve over time.

---

## Capability 5 — Basic querying

Once enough data exists, expose queries such as:

```text
How much did I spend on coffee this month?

What did I spend at H-E-B last week?

How much did fresh vegetables cost this month?

What are my most frequently purchased grocery items?
```

The first query interface does not need to be a sophisticated autonomous agent.

A simple API or CLI is acceptable before a polished chat UI exists.

---

# 5. Explicit Non-Goals for the First Iteration

Avoid turning V1 into a giant personal-finance platform.

Do not make these prerequisites for the first usable release:

- Plaid integration
- bank synchronization
- investment tracking
- retirement modeling
- tax planning
- credit score monitoring
- multi-user accounts
- social features
- public App Store release
- advanced forecasting
- autonomous purchasing decisions
- health data integration
- full “Life OS”
- elaborate dashboard design

These may become future features.

The important thing is to start collecting line-item data immediately.

---

# 6. User Workflow

## 6.1 Ideal receipt workflow

```text
PURCHASE
   |
   v
OPEN IPHONE CAPTURE APP
   |
   v
TAKE RECEIPT PHOTO
   |
   v
UPLOAD
   |
   v
"RECEIVED"
   |
   +--------------------------+
                              |
                              v
                      BACKEND PROCESSING
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
            OCR                       Image / Vision Parser
             |                                 |
             +----------------+----------------+
                              |
                              v
                       Structured Receipt
                              |
                              v
                         Normalization
                              |
                              v
                         Confidence Check
                              |
                  +-----------+-----------+
                  |                       |
               High confidence       Low confidence
                  |                       |
                  v                       v
              Auto-confirm            Review queue
                  |                       |
                  +-----------+-----------+
                              |
                              v
                            Database
```

---

# 7. Mobile Capture Client

## 7.1 Initial job of the app

The app is essentially a **receipt shutter button with secure upload**.

It should:

- request camera access,
- capture a clear image,
- optionally crop/compress,
- upload to the backend,
- handle retry if upload fails,
- show upload status,
- store temporarily if offline.

It does **not** initially need:

- AI processing on device,
- financial analytics,
- categories,
- charts,
- account balances,
- complex settings.

---

# 8. Mobile Implementation Options

There are two strong directions.

## Option A — Progressive Web App

Advantages:

- fastest path,
- minimal deployment complexity,
- accessible from iPhone,
- easy iteration,
- no App Store needed.

Disadvantages:

- camera UX may be less polished,
- iOS background behavior can be restrictive,
- offline experience requires more work,
- native integrations are less flexible.

---

## Option B — SwiftUI iPhone app

Advantages:

- excellent camera UX,
- native iOS experience,
- easier access to device capabilities,
- good long-term foundation.

Disadvantages:

- requires Xcode,
- slightly more initial setup,
- device signing / provisioning considerations.

---

## Recommendation

For the absolute fastest proof of concept:

> Begin with a tiny PWA or other minimal capture client.

If camera UX becomes annoying, move to SwiftUI.

Do not spend weeks perfecting the mobile client before the receipt pipeline exists.

---

# 9. Backend Architecture

Recommended conceptual architecture:

```text
┌─────────────────────────────┐
│        iPhone Client        │
│ camera + upload             │
└──────────────┬──────────────┘
               │ HTTPS
               ▼
┌─────────────────────────────┐
│         Upload API          │
│ validation / auth / IDs     │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│      Receipt Job Queue      │
│ pending / processing / done │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       Image Processing      │
│ crop / rotate / enhance     │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       OCR / Vision Layer    │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       Receipt Parser        │
│ structured extraction       │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       Normalization         │
│ merchants / products        │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│     Validation + Scoring    │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       Review Queue          │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│       Finance Database      │
└──────────────┬──────────────┘
               ▼
┌─────────────────────────────┐
│ Analytics / Conversational  │
│ Assistant                   │
└─────────────────────────────┘
```

---

# 10. Proposed Technology Stack

The stack should support professional software-engineering practice without making the project unnecessarily complicated.

## Backend

Recommended:

- Python
- FastAPI
- Pydantic
- SQLAlchemy or SQLModel
- Alembic
- SQLite initially
- PostgreSQL later
- pytest

Potential later additions:

- Redis
- Celery / Dramatiq / RQ
- object storage
- Docker
- background workers

---

## Data processing

Recommended:

- Python standard library where possible
- Pandas for analysis workflows, not as the core persistence layer
- Pydantic schemas for extraction contracts

---

## AI

Use a provider abstraction.

Conceptually:

```python
class ReceiptExtractor:
    def extract(self, image) -> ReceiptExtraction:
        ...
```

Do not scatter direct LLM API calls throughout the application.

The extraction implementation may eventually combine:

- OCR
- multimodal vision model
- LLM structured parsing
- merchant-specific heuristics

---

## Development environment

Yem prefers:

- Anaconda / conda for Python environment management
- VS Code as the IDE
- Git for version control

Use these deliberately rather than hiding environment management behind ad hoc commands.

Suggested environment:

```bash
conda create -n finance-ai python=3.12
conda activate finance-ai
```

Exact Python version can be adjusted for dependency compatibility.

---

# 11. Suggested Repository Structure

```text
personal-finance-ai/
│
├── README.md
├── pyproject.toml
├── environment.yml
├── .env.example
├── .gitignore
│
├── docs/
│   ├── architecture.md
│   ├── decisions/
│   └── api.md
│
├── apps/
│   ├── api/
│   │   └── ...
│   └── capture/
│       └── ...
│
├── src/
│   └── finance_ai/
│       ├── config/
│       ├── domain/
│       ├── receipts/
│       │   ├── ingestion/
│       │   ├── extraction/
│       │   ├── normalization/
│       │   └── validation/
│       ├── merchants/
│       ├── products/
│       ├── expenses/
│       ├── analytics/
│       ├── ai/
│       └── persistence/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/
│
└── data/
    ├── incoming/
    ├── processed/
    └── samples/
```

Avoid over-engineering the directory tree before code exists.

The structure can start smaller and evolve toward this.

---

# 12. Domain Model

The key conceptual entities are:

```text
Merchant
   |
   | 1..*
   v
Receipt
   |
   | 1..*
   v
ReceiptLineItem
   |
   | *..1
   v
Product
```

Additional entities can include:

```text
Category
Tag
Goal
Transaction
ReviewTask
ExtractionRun
Correction
```

---

# 13. Initial Database Schema

## merchants

```text
id
canonical_name
raw_names
created_at
updated_at
```

---

## receipts

```text
id
merchant_id
purchase_datetime
subtotal
tax
tip
discount
total
currency
payment_method
source
image_reference
status
extraction_confidence
created_at
updated_at
```

Possible `status` values:

```text
uploaded
processing
needs_review
confirmed
failed
```

---

## receipt_line_items

```text
id
receipt_id
product_id
raw_description
normalized_description
quantity
unit
unit_price
line_total
discount
category_id
extraction_confidence
created_at
updated_at
```

---

## products

```text
id
canonical_name
brand
default_category_id
created_at
updated_at
```

---

## categories

```text
id
name
parent_id
```

Support hierarchical categories later.

Example:

```text
Food
└── Groceries
    ├── Produce
    ├── Protein
    ├── Dairy
    └── Pantry
```

---

## extraction_runs

Useful for debugging AI changes.

```text
id
receipt_id
extractor_name
extractor_version
prompt_version
started_at
completed_at
raw_output
success
error
```

---

## corrections

Useful for learning from human feedback.

```text
id
entity_type
entity_id
field_name
old_value
new_value
corrected_at
```

---

# 14. Receipt Extraction Contract

The AI parser should return structured data.

Example:

```json
{
  "merchant": {
    "raw_name": "H-E-B #123",
    "canonical_name": "H-E-B"
  },
  "purchase_datetime": "2026-08-12T18:42:00",
  "currency": "USD",
  "subtotal": 42.31,
  "tax": 2.84,
  "total": 45.15,
  "items": [
    {
      "raw_description": "ORG BNNA",
      "normalized_description": "Organic Bananas",
      "quantity": 1,
      "unit": null,
      "unit_price": 2.18,
      "line_total": 2.18,
      "category": "Groceries > Produce > Fruit",
      "confidence": 0.91
    }
  ],
  "confidence": 0.94
}
```

Use schema validation.

Malformed extraction output should never silently enter the financial database.

---

# 15. Validation Rules

AI output should be checked algorithmically.

Examples:

## Arithmetic validation

```text
sum(line items)
≈ subtotal
```

Allow tolerance for:

- discounts,
- coupons,
- bottle deposits,
- taxes,
- weighted items,
- rounding.

---

## Total validation

```text
subtotal
+ tax
+ tip
- discounts
≈ total
```

---

## Required fields

At minimum:

- receipt identifier
- total
- merchant or unknown merchant
- transaction date or capture date fallback
- at least one item when itemization is expected

---

# 16. Confidence and Review

Do not use a single opaque confidence score as the only validation mechanism.

Confidence can be derived from:

- OCR certainty,
- model certainty,
- arithmetic reconciliation,
- missing values,
- ambiguity,
- merchant recognition,
- duplicate detection.

Example:

```text
if total mismatch > tolerance:
    needs_review = True

if important_field_confidence < threshold:
    needs_review = True

if no line items extracted:
    needs_review = True
```

---

# 17. Normalization

Normalization is important because receipt descriptions are ugly.

Example raw descriptions:

```text
ORG BNNA
BANANA ORGANIC
ORG BANANA
BANANAS ORG
```

Desired canonical entity:

```text
Organic Bananas
```

This allows analytics across merchants and time.

Normalization should preserve both:

```text
raw_description
normalized_description
```

Never destroy the original extracted text.

---

# 18. Categorization

Categories should support item-level analysis.

Possible starting taxonomy:

```text
Food
  Groceries
    Produce
    Meat
    Seafood
    Dairy
    Eggs
    Pantry
    Snacks
    Beverages

Dining
  Restaurant
  Coffee
  Fast Food

Transportation
  Fuel
  Maintenance
  Parking
  Rideshare

Health
  Pharmacy
  Fitness

Outdoors
  Hiking
  Camping
  Mountaineering

Entertainment
  Festivals
  Music
  Events

Home
Personal
Travel
Education
Technology
Subscriptions
Other
```

Do not obsess over a perfect taxonomy initially.

The system should support reclassification later.

---

# 19. Duplicate Detection

Eventually the same purchase may arrive from multiple channels:

- receipt photo,
- bank transaction,
- email receipt,
- online order history.

Therefore design for reconciliation.

Potential matching fields:

```text
merchant
purchase timestamp
total
payment account
last 4 digits
location
```

V1 does not need full reconciliation, but IDs and provenance should make it possible later.

---

# 20. Source / Provenance Tracking

Every expense should record where it came from.

Possible sources:

```text
receipt_photo
email_receipt
bank_transaction
manual_entry
pdf_invoice
online_order
```

This becomes important once multiple ingestion channels exist.

---

# 21. What Happens When There Is No Receipt?

The product goal is to capture **every dollar**, so receipt photography cannot be the only path forever.

Future fallback modes:

## Quick manual expense

Example:

```text
$4.25
Coffee
Gas station
```

## Voice capture

Example:

> “I just spent $7.50 on coffee at the gas station.”

## Card/bank reconciliation

Detect spending that exists in bank data but has no itemized receipt.

Then prompt later:

```text
$23.14 — Shell
No receipt found.

What was this purchase?
```

This is not required for the first implementation, but the architecture should allow it.

---

# 22. Future Ingestion Layer

The receipt camera can eventually become a **universal financial ingestion interface**.

Potential sources:

```text
Camera receipt
PDF receipt
Email receipt
Amazon order
Apple receipt
Restaurant receipt
Utility bill
Auto repair invoice
Medical bill
Travel booking
Manual entry
Bank feed
```

Think of the long-term architecture as:

```text
          MANY INPUTS
              |
              v
      Financial Ingestion API
              |
              v
          Normalization
              |
              v
       Financial Knowledge Base
              |
              v
          AI Assistant
```

---

# 23. Conversational Layer

The AI assistant should query structured financial data rather than hallucinating based on raw receipt text.

Example:

User:

> How much did I spend on coffee in July?

Correct conceptual flow:

```text
Natural language
→ query planner
→ structured database query
→ calculated result
→ natural language explanation
```

Avoid:

```text
Stuff thousands of receipts into an LLM prompt
→ hope it gets the answer right
```

Financial calculations should be deterministic whenever possible.

---

# 24. Goal Alignment Layer — Later Phase

One of the important long-term differentiators is not merely categorizing purchases but evaluating whether spending aligns with Yem's priorities.

Example:

```text
Purchase: $220 hiking equipment

Traditional budgeting app:
"You spent $220 on shopping."

Desired assistant:
"This was discretionary spending, but it aligns strongly with your outdoors priority.
Your monthly savings target is still on track."
```

Another example:

```text
Purchase: $79 impulse gadget

Assistant:
"This does not appear connected to one of your stated priorities.
You have made three similar purchases this month.
Together they total $231."
```

This should be **informational and reflective**, not moralizing.

---

# 25. Future “Regret Signal”

A useful future feature:

Several days after discretionary purchases, ask:

```text
Was this purchase worth it?

[Definitely]
[Mostly]
[Not really]
[Regret it]
```

Over time, the assistant can distinguish spending that reliably produces value from spending that tends to produce regret.

This creates individualized financial guidance rather than generic budgeting advice.

---

# 26. Why Bank Feeds Alone Are Not Enough

Bank feeds usually provide:

```text
merchant
transaction amount
transaction date
category
```

They generally do not provide complete retail basket contents.

Therefore:

```text
Bank feed = transaction ledger
Receipt ingestion = itemized ledger
```

Eventually both should be combined.

The receipt system creates the item-level dataset.

Bank feeds later help detect missing purchases and reconcile totals.

---

# 27. Storage Strategy

Receipt photos can consume space, but this is manageable.

Recommended policy:

```text
incoming image
→ processed image
→ extracted data
→ verified data
→ retention timer
→ delete or archive image
```

Do not make permanent image storage a requirement.

Store hashes / IDs / processing metadata if useful.

Long-term value comes from the structured record.

---

# 28. Security and Privacy

This project processes sensitive personal financial information.

Even though it is for one user, take security seriously.

Minimum principles:

- HTTPS for uploads
- authenticated endpoints
- secrets in environment variables
- never commit API keys
- restrict network exposure
- encrypted device storage where appropriate
- database backups
- image deletion policy
- sanitized logs
- no raw financial data in debug logs unless necessary

When the backend eventually runs on a Mac Mini at home, avoid exposing arbitrary services directly to the public internet without appropriate protections.

Potential future secure networking options may include private VPN / mesh networking, a reverse proxy, or a secured tunnel.

Do not prematurely pick infrastructure before deployment requirements are clear.

---

# 29. Development / Deployment Evolution

Yem wants to start **before the Mac Mini is available**.

Therefore architecture should support this progression.

## Stage A — Development laptop / local environment

Build:

- API
- receipt upload
- parser
- database
- tests

---

## Stage B — Temporary reachable backend

If mobile upload from outside the local network is required before the Mac Mini is available, use a safe temporary deployment approach.

The capture client should not care where the backend lives.

It only knows:

```text
POST /receipts
```

---

## Stage C — Mac Mini backend

Later move services to the Mac Mini.

Because the mobile client talks through a stable API, this should mainly be configuration rather than an app rewrite.

---

# 30. API Sketch

## Upload receipt

```http
POST /api/v1/receipts
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

Response:

```json
{
  "receipt_id": "uuid",
  "status": "uploaded"
}
```

---

## Get receipt

```http
GET /api/v1/receipts/{receipt_id}
```

---

## Get review queue

```http
GET /api/v1/reviews?status=pending
```

---

## Correct line item

```http
PATCH /api/v1/line-items/{line_item_id}
```

---

## Confirm receipt

```http
POST /api/v1/receipts/{receipt_id}/confirm
```

---

# 31. Processing State Machine

Recommended states:

```text
UPLOADED
   ↓
QUEUED
   ↓
PROCESSING
   ↓
EXTRACTED
   ↓
VALIDATING
   ↓
 ┌─────────────┐
 │             │
 v             v
CONFIRMED   NEEDS_REVIEW
               |
               v
           CONFIRMED
```

Failure state:

```text
FAILED
```

Failures should be retryable.

---

# 32. Observability

Even for a personal project, track enough metadata to debug the AI pipeline.

Useful fields:

- processing duration
- extractor version
- parser version
- prompt version
- extraction confidence
- validation result
- retry count
- error type
- model usage
- timestamp

This becomes extremely useful when extraction quality changes.

---

# 33. Testing Strategy

Use real receipt fixtures.

Create anonymized sample images if needed.

Test levels:

## Unit tests

Examples:

- total reconciliation
- category parsing
- merchant normalization
- product normalization
- confidence thresholds

## Integration tests

Examples:

```text
receipt image
→ extraction
→ schema validation
→ persistence
```

## Regression tests

A fixed receipt dataset should be reprocessed whenever extraction prompts/models change.

Track:

- field accuracy
- item count
- total reconciliation
- merchant accuracy

---

# 34. Engineering Quality Goals

This is not just a hacky utility.

One of the purposes of the project is to help Yem strengthen professional software-engineering skills.

Therefore Codex should encourage good habits:

- meaningful Git commits
- feature branches when useful
- pull-request-style self review
- automated tests
- type hints
- linting
- formatting
- environment isolation
- clear interfaces
- small modules
- documentation
- ADRs for important design choices
- incremental refactoring
- explicit error handling

Do not introduce enterprise-level complexity merely for appearance.

The goal is **professional discipline with appropriate simplicity**.

---

# 35. Git Workflow

Suggested pattern:

```text
main
  |
  +-- feature/receipt-upload
  +-- feature/receipt-parser
  +-- feature/review-queue
```

Commit examples:

```text
feat: add receipt upload endpoint
test: add receipt total reconciliation tests
feat: persist extracted receipt line items
fix: handle weighted grocery items
refactor: isolate receipt extractor interface
docs: add receipt processing architecture
```

Prefer small logical commits.

---

# 36. Environment Management

Use Conda intentionally.

Suggested files:

```text
environment.yml
pyproject.toml
```

Responsibilities:

### `environment.yml`

Development environment and interpreter.

### `pyproject.toml`

Python package metadata and Python-level dependencies/tool configuration.

Avoid undocumented global dependencies.

---

# 37. Recommended Code Quality Tooling

Possible choices:

```text
pytest
ruff
mypy or pyright
pre-commit
```

Do not add everything on day one if it blocks actual product work.

A reasonable early minimum:

```text
pytest
ruff
```

Then add type checking.

---

# 38. Architectural Rule: Domain Logic Should Not Depend on the LLM

Example:

Bad:

```python
def calculate_monthly_spend():
    return ask_llm(...)
```

Better:

```python
def calculate_monthly_spend(repository, period):
    return repository.sum_expenses(period)
```

The LLM can translate user intent into queries or explain results.

It should not be the calculator of record.

---

# 39. Architectural Rule: Make AI Replaceable

Avoid code like:

```python
client.responses.create(...)
```

throughout the domain layer.

Prefer:

```python
class ReceiptExtractionService(Protocol):
    def extract(self, image: ReceiptImage) -> ReceiptExtraction:
        ...
```

Then implement adapters.

This enables changing:

- model,
- provider,
- prompts,
- OCR approach,
- local model vs cloud model.

---

# 40. Architectural Rule: Preserve Raw + Normalized Data

For important AI-derived values keep both:

```text
raw
normalized
```

Examples:

```text
raw merchant      → "HEB 00384"
canonical merchant → "H-E-B"

raw item           → "ORG BNNA"
canonical product  → "Organic Bananas"
```

This preserves auditability.

---

# 41. Phase Plan

## Phase 0 — Repository foundation

Deliverables:

- Git repo
- conda environment
- README
- package structure
- test setup
- linting
- basic FastAPI app

Definition of done:

```text
git clone
conda env create
pytest
uvicorn ...
```

works cleanly.

---

## Phase 1 — Receipt upload

Deliverables:

- authenticated upload endpoint
- image validation
- receipt ID generation
- temporary image storage
- database receipt record
- status endpoint

Goal:

> From a phone or test client, successfully submit a receipt image.

---

## Phase 2 — Extraction pipeline

Deliverables:

- receipt extractor interface
- first extraction implementation
- Pydantic extraction schema
- validation
- extraction metadata
- failure handling

Goal:

> Image becomes valid structured receipt JSON.

---

## Phase 3 — Persistence

Deliverables:

- merchants
- receipts
- products
- line items
- extraction runs
- migrations

Goal:

> Parsed receipt becomes queryable structured data.

---

## Phase 4 — Review workflow

Deliverables:

- confidence logic
- review queue
- edit/correct endpoint
- confirm endpoint
- correction history

Goal:

> AI mistakes can be fixed quickly.

---

## Phase 5 — Mobile capture

Deliverables:

- minimal iPhone-friendly capture UI
- camera
- upload
- retry
- success confirmation

Goal:

> Actual daily use begins.

Important: Mobile capture may be pulled earlier if having real receipt data immediately is more valuable than backend polish.

---

## Phase 6 — Basic analytics

Deliverables:

- spend by product
- spend by category
- spend by merchant
- time-period filters
- frequent purchases

---

## Phase 7 — Conversational querying

Deliverables:

- natural-language question endpoint
- safe query generation
- deterministic calculations
- grounded answers

---

# 42. Suggested First Milestone

The first emotionally satisfying milestone should be:

> Photograph a real grocery receipt on the phone and see every line item appear in structured JSON.

That proves the core concept.

The next milestone:

> Persist those items and query: “How much did I spend on bananas?”

Avoid building a dashboard before this works.

---

# 43. Suggested First Vertical Slice

Build one end-to-end slice:

```text
receipt image
→ HTTP upload
→ store file
→ extraction
→ structured JSON
→ SQLite
→ GET receipt JSON
```

Do this before adding queues, complex auth, dashboards, or elaborate UI.

The simplest working pipeline will expose the real technical risks early.

---

# 44. Important Product Decisions Already Made

These decisions came from the product discussion and should not be casually reversed.

### Decision 1

**Track item-level expenses rather than only merchant-level transactions.**

Reason:

Granular financial understanding is the core value proposition.

---

### Decision 2

**Receipt images are the initial primary itemization source.**

Reason:

Bank transactions generally do not contain basket-level detail.

---

### Decision 3

**Capture should be extremely low friction.**

Reason:

The system fails if entering data becomes tedious.

---

### Decision 4

**The phone client should be simple.**

Reason:

Processing belongs in the backend and should be independently replaceable.

---

### Decision 5

**Receipt images can eventually be deleted after confirmation.**

Reason:

Structured records are the durable asset.

However images should initially be retained long enough for verification/debugging.

---

### Decision 6

**The ingestion system should eventually accept more than receipt photos.**

Future examples:

- email
- PDFs
- bills
- online orders
- manual entry
- bank feeds

---

### Decision 7

**Do not combine this with the separate health assistant project.**

The finance project should remain independently designed.

It may interoperate with a larger personal AI ecosystem later.

---

# 45. What Matters Most to Yem

Codex should optimize for these preferences:

## Extremely detailed spend capture

The goal is **every dollar**, ideally down to the purchased item.

---

## Real daily usefulness

This is not merely a portfolio demo.

Yem intends to actually use it.

---

## Low friction

If recording spending becomes a chore, the system will fail behaviorally even if the engineering is impressive.

---

## Iterative development

Start small.

Ship a narrow slice.

Use it.

Learn.

Then expand.

---

## Professional engineering growth

This project should reinforce:

- Python development
- backend architecture
- APIs
- databases
- testing
- Git
- environment management
- production-minded thinking
- AI integration
- system design

---

## Portfolio quality

The architecture and repo should eventually be clean enough to demonstrate software-engineering ability.

Privacy-sensitive personal data should never be part of a public portfolio repository.

Use synthetic fixtures for demos.

---

# 46. How Codex Should Work With Yem

Codex should behave like a senior engineer pairing with a developer.

## Preferred style

- Explain architectural choices.
- Avoid dumping huge unexplained codebases.
- Build incrementally.
- Keep components testable.
- Ask Yem to run commands when local execution matters.
- Explain failures rather than patching blindly.
- Encourage Git commits at meaningful checkpoints.
- Preserve a running list of architectural decisions.
- Prefer simple solutions until complexity is justified.

---

# 47. Codex Guardrails

Codex should NOT:

- jump directly into microservices,
- introduce Kubernetes,
- add Kafka without a demonstrated need,
- create ten services for a single-user app,
- build complex auth before an end-to-end receipt works,
- couple domain logic directly to an LLM provider,
- use Pandas as the transactional database,
- store only AI-normalized fields and discard raw values,
- delete receipt images before extraction is verified,
- let the LLM perform arithmetic that SQL/Python can perform deterministically,
- leak secrets into Git,
- commit real personal receipts to the repository.

---

# 48. First Codex Session — Recommended Task

Start with repository initialization and the smallest vertical slice.

A good first session objective:

> Create the Python project skeleton, Conda environment, FastAPI service, SQLite persistence, and a receipt upload endpoint that accepts an image and creates a receipt record with status `uploaded`.

Do **not** implement advanced AI extraction yet unless the foundational path is working.

Expected result:

```text
POST receipt image
→ 201 Created
→ receipt UUID
→ receipt record in SQLite
→ stored image reference
→ GET receipt returns metadata
```

Tests should cover the upload path.

---

# 49. Suggested Initial Backlog

```text
P0
[ ] Initialize Git repository
[ ] Create Conda environment
[ ] Create Python package
[ ] Add FastAPI
[ ] Add pytest
[ ] Add Ruff
[ ] Add SQLite
[ ] Add migrations
[ ] Create Receipt model
[ ] Create upload endpoint
[ ] Validate image MIME type
[ ] Generate receipt UUID
[ ] Persist receipt metadata
[ ] Store uploaded image
[ ] Add receipt status endpoint
[ ] Add tests

P1
[ ] Define ReceiptExtraction Pydantic schema
[ ] Define ReceiptExtractor interface
[ ] Implement first AI extractor adapter
[ ] Add arithmetic validation
[ ] Persist extracted line items
[ ] Add merchant normalization
[ ] Add product normalization
[ ] Add confidence scoring
[ ] Add review state

P2
[ ] Build minimal phone capture client
[ ] Add camera workflow
[ ] Add upload retry
[ ] Add offline temporary queue
[ ] Add review UI
[ ] Add basic analytics

P3
[ ] Add natural-language financial querying
[ ] Add bank reconciliation
[ ] Add email/PDF ingestion
[ ] Add goal alignment
[ ] Add regret feedback
```

---

# 50. Immediate Definition of Success

The project is successful at the first stage when Yem can do this:

```text
1. Buy groceries.
2. Photograph the receipt.
3. Submit it.
4. Walk away.
5. Later see:

H-E-B — $58.37

- bananas — $2.18
- onions — $4.12
- rice — $8.99
- yogurt — $6.49
...
```

And shortly after:

```text
Question:
How much have I spent on bananas this month?

Answer:
$14.62
```

That is the core product.

Everything else is expansion.

---

# 51. Suggested First Prompt to Codex

Copy/paste this after providing Codex this handoff:

> We are starting implementation of the Personal AI Finance Assistant described in this handoff. Treat this document as the product and architectural context.
>
> I want to build this professionally but incrementally. I use Conda for Python environment management, VS Code as my IDE, and Git for version control.
>
> Start with Phase 0 and the first vertical slice only. Before writing a large amount of code, inspect the current repository state. Then propose the smallest implementation that gets us to:
>
> `receipt image → FastAPI upload → SQLite receipt record → stored image → receipt metadata endpoint`
>
> Use tests from the beginning. Keep the architecture simple and explain important decisions. Do not introduce infrastructure we do not yet need. At each meaningful milestone, suggest a Git commit message.
>
> Once the vertical slice is working, stop and summarize what we built, the directory structure, how to run it, how to test it, and what the next smallest milestone should be.

---

# 52. Final Principle

When choosing between a sophisticated architecture and a system Yem will actually use every day:

> **Choose the system that gets used.**

The immediate competitive advantage of this project is not complexity.

It is creating a reliable, low-friction, item-level financial history from everyday spending.

Once that dataset exists, the intelligence layer becomes dramatically more valuable.
