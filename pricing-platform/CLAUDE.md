# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PERMANENT PROJECT INSTRUCTION

You are the principal software architect and senior full-stack engineer working on a
multi-tenant B2B SaaS application called:

Retail Pricing Intelligence Platform.

The application helps retailers manage:

- Products
- Inventory
- Pricing
- Pricing Rules
- Promotions
- Multiple Stores
- ESL devices
- ERP/POS integrations
- Multiple output channels
- AI pricing recommendations

Technology stack:

FRONTEND:
- React JS
- Vite
- Material UI
- JavaScript
- React Router
- TanStack Query
- Axios
- React Hook Form
- Zod or Yup

BACKEND:
- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- Celery

DATABASE:
- MySQL 8

INFRASTRUCTURE:
- Docker
- AWS RDS MySQL
- AWS S3
- Redis
- Celery
- MQTT
- AWS CloudWatch
- AWS Secrets Manager

ARCHITECTURE PRINCIPLES:

1. Use a modular monolith architecture.
2. Do not create microservices during the MVP.
3. Every module must be independently organized.
4. Use service/repository patterns where useful.
5. Keep business logic out of API route files.
6. Keep database logic out of frontend code.
7. Use API versioning.
8. All APIs must be under /api/v1.
9. Use UUID identifiers.
10. All timestamps should be UTC.
11. Implement soft deletes where required.
12. Maintain audit logs for important changes.
13. Use database migrations through Alembic.
14. Do not use database auto-creation in production.
15. Use environment variables for configuration.
16. Never hard-code secrets.
17. Validate every API request using Pydantic.
18. Return consistent API response structures.
19. Implement structured error handling.
20. Write tests for critical business logic.
21. Use tenant isolation in all relevant database queries.
22. Never expose another organization's data.
23. Every future external integration must use an adapter interface.
24. Every future ESL integration must use a vendor abstraction layer.
25. Every future AI action must be auditable.
26. AI must not bypass deterministic pricing guardrails.
27. Do not introduce new dependencies without justification.
28. Do not modify unrelated modules.
29. Before implementing major changes, inspect the existing codebase.
30. After implementation, run tests and report errors.

FRONTEND RULES:

1. Use functional components only.
2. Use reusable components.
3. Do not duplicate API logic.
4. Create feature-specific folders.
5. Use React Query for server state.
6. Use Material UI components consistently.
7. Support loading states.
8. Support empty states.
9. Support error states.
10. Use form validation.
11. Implement responsive layouts.
12. Follow accessibility practices.
13. Do not put business logic directly into page components.

BACKEND RULES:

1. Routes → Services → Repositories → Database.
2. Routes should remain thin.
3. Services contain business logic.
4. Repositories contain database access logic.
5. Use SQLAlchemy ORM.
6. Avoid raw SQL unless necessary.
7. Add appropriate database indexes.
8. Use transactions for multi-table operations.
9. Use background jobs for long-running operations.
10. Do not make AI calls inside database transactions.

Before starting implementation:

- Review the existing repository.
- Explain the implementation plan.
- List files that will be created.
- List files that will be modified.
- Identify database migrations required.

After implementation:

- Run the relevant tests.
- Run linting if configured.
- Report implementation details.
- Report files changed.
- Report API endpoints added.
- Report database tables added or modified.
- Report anything incomplete.

Do not over-engineer.

Implement only the current requested phase.
Do not implement future phases unless explicitly requested.

## Project

Retail Pricing Intelligence Platform — a multi-tenant B2B SaaS app for retailers to manage
products, inventory, pricing, pricing rules, promotions, multiple stores, ESL devices,
ERP/POS integrations, output channels, and AI pricing recommendations.

**Current state: Phases 0–15 complete (from upstream clone). Product URL Fetcher, QR/PDF
label redesign, Label Template System (Stage 2), analytics cache fix, Pricer Plaza API
integration, ESL Integration edit/delete, a full responsive redesign, and the merged
ESL Devices Integration workflow (vendor-first: create integration + store, then manage
its devices) added post-clone. AI is still unimplemented.**
logout), RBAC (6 seeded system roles, 39 permissions), a minimal user-management
foundation (`GET /api/v1/users`, tenant-scoped), Store Management, Category/Product
Management, Multi-store Inventory Management, Product/Inventory Bulk Import
(CSV/XLSX, background processing, per-row error reporting), the deterministic Pricing
Engine, the Output Orchestration Engine, the ESL Device Platform Foundation, the
Third-Party ESL Integration Framework, the Enterprise Integration Hub, and a
Product URL Fetcher feature are implemented — see
`app/core/rbac.py` for the role/permission constants and `app/api/v1/stores.py` /
`app/api/v1/products.py` for the CRUD pattern new tenant-scoped resources should
follow. Categories form a self-referential hierarchy (`parent_id`) and are hard-deleted
(not soft-deleted) — `CategoryService.delete` blocks deletion of a category that still
has subcategories or products. `Inventory.quantity_on_hand` is only ever changed
through `POST /api/v1/inventory/bulk-update` (never `PUT`), which enforces "no negative
stock unless explicitly flagged per-request" and writes an `InventoryAdjustment` audit
row. "Overstock" is a documented heuristic (`on_hand > reorder_point *
OVERSTOCK_MULTIPLIER` in `app/repositories/inventory_repository.py`), not a real
threshold column — there's no `max_stock_level` field.

Bulk import (`app/services/import_service.py`): `POST /api/v1/imports` uploads a file,
stores it via `app/storage/` (an `S3StorageAdapter`/`LocalFilesystemStorageAdapter`
pair selected by `get_storage_adapter()` — S3 when `S3_BUCKET_NAME` is set, a local
`var/storage/` directory otherwise, so imports work without real AWS infra in dev), and
parses just the header row. `POST /api/v1/imports/{id}/start` (not in the literal Phase
5 endpoint list, but required — nothing else exists for the wizard's "map columns" step
to submit to) takes the column mapping and dispatches
`app.tasks.imports.process_import_job_task`, a thin Celery wrapper around
`import_service.process_import_job` (call this directly with a `db=` session — e.g. in
tests — to run it with no Celery/Redis at all). Validation and import happen together
in one background pass per row (a SAVEPOINT per row isolates one row's failure from the
rest); there is no separate manual "commit valid rows" step. Every row failure is
persisted to `ImportRowError`, not just logged. Local dev has no Redis running, so
queued jobs stay `queued` until a worker is started — see the Celery command in
`infrastructure/docker-compose.yml`'s `celery_worker` service.

Pricing engine (`app/services/pricing_engine.py`): `Price` rows hold one priced period
per product (optionally store-specific); `compute_display_status()` derives
ACTIVE/SCHEDULED/EXPIRED at read time from `effective_from`/`effective_to` (mirrors the
Inventory status pattern) rather than persisting it, and normalizes naive datetimes to
UTC before comparing (SQLite drops tzinfo on round-trip even for
`DateTime(timezone=True)` columns; MySQL doesn't). `PricingRule.rule_type` (10 values —
Fixed Price, Percentage Discount, Fixed Discount, Margin Based, Cost Plus, Inventory
Based, Time Based, Store Specific, Promotion, Clearance) is a categorization label only;
what the engine actually computes comes from the separate, decoupled
`actions_json.kind` (5 values — `app/schemas/pricing_rule.py`'s `ActionKind`), validated
by a Pydantic field validator. `evaluate_for_product()` fetches in-force rules ordered by
priority, matches each against `conditions_json` (product/category/store scope,
min/max quantity), applies its action then its `constraints_json` (min/max price, min
margin, max discount, rounding — including a `charm_99` X.99 mode), and returns a full
`RuleTestResult` trace consumed by both `POST /pricing/rules/{id}/test` and the frontend
test-mode page. Every price create/update that changes `selling_price` writes a
`PriceHistory` row (`app/services/price_service.py`); all money math uses `Decimal`,
quantized to `Decimal("0.0001")`. No dedicated Price management UI exists — only the
rule builder (`RuleForm.jsx`) and test-mode page, per the literal Phase 6 frontend spec.

Output orchestration (`app/outputs/`, `app/services/output_job_service.py`): every output
type (ESL simulator, QR code, printable PDF label, public web display) implements the
`OutputAdapter` interface (`app/outputs/base.py`: `validate_configuration`,
`render_payload`, `send_update`, `get_status`), selected by `OutputChannel.output_type`
via `app/outputs/registry.py` — services never depend on a concrete output type. A real
ESL vendor/hardware integration is explicitly out of scope for this phase; the "ESL
Simulator" only produces the data the React frontend renders as a fake label
(`ESLSimulatorPreview.jsx`) — no MQTT/vendor protocol involved. `OutputChannel.store_id`
is not in the literal Phase 7 DB spec, but the Output Management UI's field list
requires a Store field — added as a nullable FK (NULL = organization-wide), same
precedent as `Product.brand` in Phase 3. `output_job_service.create_job` dispatches via
`app.tasks.outputs.process_output_job_task` (Celery, with the same broker-reachability
pre-check/graceful-pending-fallback as imports/pricing); `create_job`/`retry_job`
commit the transaction BEFORE calling Celery's `.delay()` — the worker is a separate
OS process reading the committed DB, so dispatching first lets it race the
request-scoped `get_db()` commit and "not-found"/"skip" the still-uncommitted job,
leaving it stuck pending forever (caught by the live MySQL smoke test, not the suite,
since tests run client and worker in the same process — the same gap as the Phase 10
webhook `pushed_records` bug); `resolve_display_price()`
reuses `pricing_engine.evaluate_for_product()` so an output always reflects the fully
rule-applied price, not just the raw stored `Price` row. QR/PDF artifacts are generated
(via `app/outputs/qr_render.py` and `reportlab`) and returned as base64 directly on
`OutputJob.payload` rather than through a file-download endpoint — the app has no generic
file-serving endpoint yet, and inventing one was out of scope for this phase. The shared
`render_qr_png()` helper in `app/outputs/qr_render.py` produces the QR PNG used by both
the QR output adapter and the PDF label adapter (so the QR image on printed labels is
identical to the standalone QR output). The QR encodes the product's `product_url` field
(the retailer source page set via the Product URL Fetcher or the product form) when
present; if the product has no `product_url`, the QR encodes an empty string (valid blank
QR image). The PDF label adapter (`app/outputs/pdf_label.py`) draws a three-column
black-and-white shelf label: product name + price on one side, a bordered unit-price
box in the center, and an embedded QR code on the other side, with a store-name banner
on top or bottom and a shelf-number badge (`product.shelf_id`) in the top-right corner.
All layout elements are configurable per output channel: `show_qr`, `qr_position`
(left/right), `qr_size_mm`, `show_unit_price`, `banner_position` (top/bottom), and
`banner_text` (store name override). The PDF adapter never queries the DB — all inputs
come from `OutputRenderContext`. **All four layout combinations (banner top/bottom × QR
left/right) render cleanly:** the badge moves to the opposite corner from the banner
(top banner → badge bottom-right; bottom banner → badge centered below QR), and a
3 mm extra top margin when the banner is at the bottom prevents the product name from
clipping the border. `GET /api/v1/public/price/{product_id}`
(`app/api/v1/public.py`) is unauthenticated by design — it's the target Web Output
links point to — and exposes only customer-facing fields
(`app/schemas/public.py`'s `PublicPriceDisplay`).

Label template system (`app/models/label_template.py`, `app/services/label_template_service.py`,
`app/api/v1/label_templates.py`): a standalone org-scoped `LabelTemplate` entity holds
`colors` (JSON dict of up to 7 color keys — background, border, text, banner, unit_border,
sublabel, placeholder — each a hex string) and an optional `background_image_url` (opaque
storage reference). `OutputChannel` has a nullable FK `label_template_id`
(ON DELETE SET NULL) — NULL means the adapter's built-in defaults, so existing channels
and rendering are byte-identical. Template data is resolved **once** in
`output_job_service._run` and carried into `OutputRenderContext` as `template_colors` and
`template_background_image_url`; adapters are DB-free. The PDF label adapter merges
`context.template_colors` over `_DEFAULT_COLORS` key-by-key, and if a background image URL
is present, downloads it via `get_storage_adapter()` and draws it behind text/QR/unit-box/
banner inside a try/except — any failure (missing file, bad bytes) skips the image and
renders the plain color background (a job never fails for its decoration). The full template
builder (fonts, layout, spacing) is designed to be added later: `LabelTemplate` gains
additional columns, `OutputRenderContext` gains matching optional fields, and `_run` stays
the single resolution point.

ESL device platform (`app/integrations/base.py`'s `ESLVendorAdapter`, `app/integrations/
esl_simulator/adapter.py`, `app/services/device_*.py`): `device_vendors`/`device_models`
are global platform catalog data (no `organization_id` — seeded via a data migration,
`alembic/versions/9c4e2a6f8d1b_...`, with one vendor/model: `DeviceVendor(code=
"esl_simulator")`); `devices`/`device_assignments`/`device_sync_logs` are tenant data.
`device_assignments`/`device_sync_logs` have no `organization_id` column (per the
literal Phase 8 spec) — tenant scoping is enforced by joining through `device_id` to
`Device.organization_id` (see `DeviceAssignmentRepository`/`DeviceSyncLogRepository`).
`Device.store_id` is required (Device Form's "Store*"); assigning a new product to a
device (`device_assignment_service.create_assignment`) ends any existing active
assignment first — a device can only display one product at a time — and immediately
triggers a sync so the simulator reflects it. Every `ESLVendorAdapter` (`register_device`,
`discover_devices`, `assign_product`, `unassign_product`, `update_price`,
`update_template`, `get_status`, `get_health`, `sync_device`) is implemented by
`ESLSimulatorAdapter`, resolved via `app/integrations/registry.py` by
`DeviceVendor.code`; `discover_devices()` satisfies the interface but isn't wired to any
UI (the Device Form takes a manually-entered Device Identifier instead). The MQTT flow
("Pricing Engine -> Output Job -> ESL Adapter -> MQTT -> ESL Simulator ->
Acknowledgement") is real but best-effort: `app/services/mqtt_publisher.py` publishes to
`{prefix}/{organization_id}/store/{store_id}/device/{device_id}/update` via `paho-mqtt`
when a broker is reachable (`infrastructure/docker-compose.yml`'s `mqtt` service, not
started by default), but the device's acknowledgement is always simulated synchronously
regardless — there's no physical hardware to wait on. The "React ESL simulator"
(`DeviceESLPreview.jsx`) does not hold a live MQTT-over-WebSocket connection (no broker
with a websocket listener is available in this environment); it polls
`GET /api/v1/public/price/{product_id}` (the same Phase 7 public endpoint, reused so the
preview always reflects the fully rule-applied price) and device health, refreshing
after any sync/assignment via query invalidation — a genuinely live broker-pushed
version could replace this later without changing the adapter interface.
`device_sync_logs.output_job_id` is nullable and not yet populated automatically from an
Output Job dispatch — only the manual "Resync" and assignment-triggered sync paths are
wired in this phase; wiring Phase 7 output jobs to auto-trigger a device sync was out of
scope (not in the Phase 8 deliverable list).

Third-party ESL integration framework (`app/integrations/esl/`, `esl_integrations` table,
`app/services/esl_integration_service.py`): a *second*, separate adapter interface —
`ESLIntegrationAdapter` (`app/integrations/esl/base.py`), async, 6 methods
(`test_connection`, `discover_devices`, `push_price`, `push_template`,
`get_device_status`, `get_sync_status`) — matching the Phase 9 spec's example almost
verbatim but named differently to avoid colliding with Phase 8's already-implemented,
synchronous, per-device `ESLVendorAdapter` in `app/integrations/base.py`: Phase 8's
interface operates once a device already exists in our `devices` table (day-to-day
health/resync), while this one operates at the vendor *connection* level (what the
Integration Setup Wizard drives) — see the module docstring in
`app/integrations/esl/base.py` for the full reasoning. `ESLIntegration.
configuration_encrypted` is Fernet ciphertext (`app/core/crypto.py`,
`ESL_CREDENTIALS_ENCRYPTION_KEY`) — `ESLIntegrationOut` has no field for it or for raw
credentials at all, so the API can never echo them back once saved. `integration_type`
(`mock` | `mqtt` | `api`) selects the adapter *mechanism* independently of which
`device_vendors` catalog entry (`vendor_id`) the integration is for —
`app/integrations/esl/registry.py`'s `get_integration_adapter()` resolves `mock` to
`MockVendorAdapter` (canned always-succeeds responses, so the whole 8-step wizard is
testable without a real vendor account or broker) and `mqtt` to `MQTTESLAdapter`
(genuine `paho-mqtt` publish when a broker is reachable, honestly reports failure in
`test_connection()` otherwise) regardless of vendor, while `api` dispatches per
`DeviceVendor.code` to one of five vendor stub adapters
(`app/integrations/esl/vendor_stubs.py`: Vusion, Hanshow, SOLUM, ZKong — each fails
with an explicit "requires a signed partner API/SDK agreement not available in this build"
message — selecting one of these vendors is not a claim of real integration, per the spec's
"do not claim integration with a vendor unless an actual supported API/SDK/partner
integration is available." Pricer is the exception: `registry.py` dispatches to
`pricer_adapter.PricerAdapter` (a real Plaza API integration) instead of its stub. `Device.esl_integration_id`
is not in the literal Phase 8 DB spec — added (nullable FK) so a device imported via
the wizard's "Import Devices" step is traceable to the integration it came from.
Phase 8's `app/integrations/registry.py` (the per-device sync layer) now falls back to
the built-in simulator for any vendor code it doesn't have a dedicated sync adapter for
(i.e. every vendor except `esl_simulator`) rather than failing device creation/health
lookups outright — day-to-day device-management simulation works the same regardless of
which vendor catalog entry a device belongs to; real vendor communication for those
devices happens through this phase's `ESLIntegrationAdapter` layer instead. The wizard's
"Test Price Update" step (and every `push_price`/`push_template` call) still resolves
the price via `output_job_service.resolve_display_price()`, so it's the fully
rule-applied price like every other output/device path.

Pricer Plaza integration (`app/integrations/esl/pricer_adapter.py`,
`app/integrations/esl/pricer_simulator.py`): the Pricer ESL vendor (`device_vendors.code
= "pricer"`) now has a real `PricerAdapter` (implements `ESLIntegrationAdapter`) that
talks to the live Pricer Plaza API (`https://api.pricer-plaza.com`), replacing the
former stub adapter. `PricerClient` handles OAuth2 `client_credentials` token auth with
automatic caching and 401 refresh; the adapter exposes `test_connection`, `discover_devices`,
`push_price`, `push_template`, `get_device_status`, and `get_sync_status`. Each call reads
`ESLIntegration.base_url` (defaulting to the Plaza production URL) and the vendor-specific
credentials (`client_id`, `client_secret`, `store_id`) from `ESLIntegration
.configuration_encrypted` — these three credential fields are presented by the frontend
wizard (`CREDENTIAL_FIELDS_BY_VENDOR_CODE.pricer`) instead of the generic api_key/secret
fields used by other vendors. A standalone FastAPI simulator (`python -m
app.integrations.esl.pricer_simulator`, port 8090) mirrors the Plaza API's response schemas
in-memory, so the full integration can be tested locally without a Plaza tenant or physical
devices: set `base_url` to `http://localhost:8090` in the wizard's Step 2 and use the
simulator's default test credentials (`test-client` / `test-secret` / `store-1`).
`registry.py` now imports `PricerAdapter` from `pricer_adapter` (not from
`vendor_stubs.py`); the four remaining vendor stubs (Vusion, Hanshow, SOLUM, ZKong) are
unchanged. Tests: `test_pricer_adapter.py` (15 mock-based unit tests) and
`test_pricer_e2e.py` (15 live-simulator E2E tests) — both fully passing.

Enterprise Integration Hub (`app/integrations/base.py`'s `IntegrationAdapter`,
`app/integrations/hub/`, `app/models/integration*.py`, `app/services/integration_*.py`):
generic ERP/POS/ecommerce integrations, distinct from Phase 9's ESL-specific
`esl_integrations`/`ESLIntegrationAdapter` — this is the Phase 0 `IntegrationAdapter`
stub (never previously implemented anywhere) filled in for real. External data is never
mapped straight onto the domain tables: a source record is first transformed
(`app/services/integration_mapping_engine.py`, driven by that integration's
`IntegrationMapping` rows) into one of five canonical shapes
(`app/schemas/canonical.py` — `CanonicalProduct/Price/Inventory/Promotion/Store`, all
`extra="forbid"` so a mistyped `canonical_field` surfaces as a sync error rather than
silently dropping data), then reconciled into the real Product/Price/Inventory/Store
tables by `app/services/integration_apply_service.py`. `CanonicalPromotion` has no
apply path — the platform has no persisted Promotion entity (`pricing_rules.rule_type
="promotion"` is a categorization label, not a table) — so applying one fails clearly
rather than silently no-op'ing. `Integration.provider` (not `integration_category`,
which is just a UI-facing business label) selects the adapter via
`app/integrations/hub/registry.py`: `csv`/`rest_api`/`webhook` are fully implemented
(the REST adapter is a genuinely generic HTTP client — no vendor request/response shape
hard-coded — and the CSV adapter reads a real local-file-or-URL from
`credentials["base_url"]`), while `sap`/`oracle` are catalog entries whose adapter fails
every call with an explicit "not available" message, per "do not implement SAP or
Oracle directly yet" (same honesty pattern as Phase 9's ESL vendor stubs).
`IntegrationSyncJob.entity_type` and `.pushed_records` are not in the literal Phase 10
DB spec — `entity_type` is required because a sync job genuinely can't run or be
retried without knowing which canonical shape to fetch/apply, and `pushed_records`
exists because a webhook-type integration has no way to actively "pull" data (it
arrives by push on `POST /integrations/{id}/sync`), and that payload must be durably
readable by whichever process actually runs the sync — the Celery worker is a
*separate OS process* from the API server that created the job row, so an in-memory
dict keyed by job id (tried first) silently discarded every webhook payload the moment
a real worker process picked up the task; this was caught by the live MySQL smoke test
(restarting the dev server to simulate a distinct worker process), not by the automated
test suite, since tests run client and worker in the same process. `pushed_records` is
deliberately left on the job row after processing (not cleared) so retrying a webhook
job reuses the same payload by default. Field-mapping and sync-job-retry endpoints
(`POST /integrations/{id}/mappings`, `GET .../mappings`, `DELETE .../mappings/{id}`,
`POST /integrations/{id}/jobs/{job_id}/retry`) are additive beyond the four literally
listed endpoints — the "Add field mapping UI" and "Create retry logic" requirements
can't function without them, same precedent as every prior phase's UI-required-but-
unlisted endpoints (e.g. Phase 5's `/imports/{id}/start`).

Product URL Fetcher (`app/services/product_url_fetcher.py`, `POST /products/fetch-from-url`,
new columns on `products`): lets the person at the POS paste a retailer product page URL
(e.g. a Walmart item page) and have the create form pre-fill product fields instead of
typing name/price/image/brand/SKU by hand. `Product` gained three **nullable** columns —
`product_url` (String 500, the source page), `qr_id` (String 150) and `shelf_id`
(String 150) — added by the hand-written migration `790934a4508d`. All three are nullable
so the explicit `Product(...)` constructors in `import_service.py` and
`integration_apply_service.py` (which don't set them) and existing rows are unaffected.
`POST /products/fetch-from-url` (`app/api/v1/products.py`) takes a `ProductUrlFetchRequest`,
is gated behind `products.create`, and returns a `ProductUrlSuggestion` (all fields
`str | None` plus an `error` field); it never writes to the database — the frontend
pre-fills the form and the user reviews/edits before Save. The service (`httpx`, timeout
12s, browser-like User-Agent, `follow_redirects`) parses the page with Python's stdlib
`html.parser` — deliberately no BeautifulSoup dependency — collecting `<title>`, OpenGraph
meta (`og:title/description/image/site_name`) and `<script type="application/ld+json">`
blocks, then walks JSON-LD for a schema.org `Product` node (`name`, `offers.price` +
`priceCurrency` handling dict-or-array, `brand.name`, `sku`, `gtin/gtin8/gtin12/gtin13/
gtin14`, `image`) and falls back field-by-field to OpenGraph. Extraction success is judged
by a *substantial*-field heuristic (`_PRODUCT_SIGNAL_FIELDS`): at least one of price/brand/
sku/barcode/image must be extracted — a bare `<title>` (which every page has) is **not**
treated as product data, so a blog post errors out honestly instead of pre-filling a junk
name. Failure modes return `error` (network blocked / timed out, or page loaded but no
product data) with HTTP 200 so the UI can show a specific message and the user falls back
to manual entry; the service never raises `httpx.HTTPError` out. `url` is normalized
(prepend `https://` when no scheme). Price is returned as a clean numeric string (first
decimal match) so it drops straight into the decimal-validated form field. Frontend:
`features/products/` (`api.js` `fetchProductFromUrl`, `hooks.js` `useFetchProductFromUrl`,
`validation.js` adds the 3 optional-string rules) and `ProductForm.jsx` — Product URL
TextField with a **Fetch** button beside it that calls the endpoint and
`setValue`-pre-fills every non-null suggestion field (`product_url` too), showing a
success/"filled in N fields — review before saving" or error `Alert`. `ProductDetailsPage.jsx`
shows Product URL (as a clickable link), QR ID, Shelf ID in Basic Information. Known limit:
only server-side structured data is read (no JS rendering) — sites that render everything
client-side won't yield data, and anti-bot protection (e.g. Akamai) may block the fetch.
Tests: `tests/test_product_url_fetcher.py` (6 unit tests, `httpx` mocked, no network).

Analytics dashboard (`GET /api/v1/analytics/dashboard`, `app/services/analytics_service.py`):
`_compute_from_snapshots` **always recomputes today** on read (today's snapshot is never
final — a price change / inventory adjustment / device sync that lands moments ago must show
up immediately), and past days are pre-aggregated into `analytics_snapshots`. The Redis
response cache (120s TTL) therefore covers **only settled day-ranges that end strictly before
today** (`cacheable_range = date_to < today`); anything spanning today bypasses the cache and
recomputes. Do not reintroduce caching for today-inclusive ranges — that served stale
same-day data for up to 120s and is caught by
`tests/test_analytics.py::test_price_change_count_and_average` (two back-to-back unfiltered
dashboard reads, the second must reflect a just-made price change).

AI is still unimplemented. Implement only the phase you are asked for; do not build
ahead of what's requested.

## Commands

### Backend (`backend/`)

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows; use .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload   # serves http://localhost:8000/api/v1/...
```

Tests (pytest, configured via `pyproject.toml`, `pythonpath = ["."]`):

```bash
pytest                                          # full suite
pytest tests/test_health.py::test_health_check_returns_ok   # single test
```

Lint (ruff, configured via `pyproject.toml`):

```bash
ruff check app tests
```

Migrations (Alembic — `backend/alembic/`):

```bash
alembic revision --autogenerate -m "add <table>"
alembic upgrade head
```

`alembic/env.py` reads the DB URL from `Settings` (not `alembic.ini`) and targets
`Base.metadata` via `import app.models` (every model is registered through
`app/models/__init__.py` — add new model modules there, not just in `alembic/env.py`).
Two migrations exist: a schema migration (organizations/users/roles/permissions/
user_roles/role_permissions) and a hand-written data migration that seeds the 25
permissions and 6 system roles (`alembic/versions/eaa27d8a5e16_...`) — see
`app/core/rbac.py` for the literal values it mirrors. `Base.metadata.create_all` is never
used outside tests; schema changes always go through Alembic.

### Frontend (`frontend/`)

```bash
npm install
cp .env.example .env
npm run dev       # http://localhost:5173
npm run build
npm run lint       # eslint . (dist/ and node_modules/ excluded via .eslintignore)
```

No frontend test runner is configured yet.

### Full stack

```bash
cd infrastructure
docker compose up --build   # mysql8, redis, backend, celery_worker, frontend
```

## Architecture

Modular monolith (deliberately not microservices for the MVP — every module lives in
this one repo/deployable, organized independently).

### Backend layering

Strict one-way dependency chain, enforced by convention across every module:

```
app/api/v1/*  →  app/services/*  →  app/repositories/*  →  app/db (SQLAlchemy)
```

- **Routes** (`app/api/v1/`) stay thin: request validation via Pydantic schemas and
  delegation only, no business logic. `app/api/v1/router.py` is the single place that
  aggregates per-feature routers under the `/api/v1` prefix set in `app/main.py`.
- **Services** (`app/services/`) hold business logic and raise `AppError` subclasses
  (`app/core/exceptions.py`: `NotFoundError`, `ConflictError`, `ForbiddenError`, or
  `AppError` directly) rather than HTTP exceptions — these are translated into the
  standard error envelope by the global handlers registered in
  `register_exception_handlers()`.
- **Repositories** (`app/repositories/`) are the only layer that talks SQLAlchemy.
  `BaseRepository` (`app/repositories/base.py`) filters out soft-deleted rows only for
  models that have a `deleted_at` column (checked via `hasattr`, since `Role`,
  `Permission`, `UserRole`, `RolePermission` don't). Tenant-scoped repositories
  (`UserRepository.list_by_organization`, etc.) additionally filter by
  `organization_id` — this is the enforcement point for "never expose another org's
  data." `app/dependencies/auth.py` (`get_current_user`, `require_permission(code)`) is
  the RBAC enforcement point at the route layer.

### Response envelope

Every endpoint returns the same shape via `app/core/responses.py`:
`APIResponse[T]` (`{success, data, meta}`) on success, `APIErrorResponse`
(`{success, error: {code, message, field}}`) on failure. The error envelope is produced
automatically by the exception handlers in `app/core/exceptions.py` for `AppError`,
`RequestValidationError`, and any unhandled exception — services should raise, not
build error responses by hand.

### Models

All ORM models compose the mixins in `app/models/mixins.py` rather than redefining
these columns:

- `UUIDPrimaryKeyMixin` — UUID primary keys everywhere, no auto-increment ints.
- `TimestampMixin` — `created_at`/`updated_at`, always UTC (`utcnow()` helper).
- `SoftDeleteMixin` — `deleted_at` nullable + `is_deleted` property; hard deletes are
  not used for domain data.
- `AuditMixin` — `created_by`/`updated_by` UUID columns (still no FK to `users.id`;
  `User` now exists, but no model uses this mixin yet — wire the FK when one does).
- `CreatedAtMixin` — `created_at` only, for link/association tables (`UserRole`,
  `RolePermission`) that don't track updates.

### Integrations and ESL devices

`app/integrations/base.py` defines two abstract interfaces that every future vendor
integration must implement, so services never depend on a specific vendor:

- `IntegrationAdapter` — ERP/POS systems and output channels (`connect`, `sync`,
  `health_check`).
- `ESLVendorAdapter` — electronic shelf label vendors (`push_price_update`,
  `get_label_status`), keeping vendor-specific protocol details (e.g. MQTT topic shape)
  out of pricing/service code.

Concrete vendor implementations belong in their own submodule under
`app/integrations/<vendor>/`.

### AI actions

`app/ai/base.py` defines the contract every AI-driven pricing action must follow:

- `PricingGuardrail.validate()` — deterministic, non-AI code that checks a proposed
  price (min margin, max discount, bounds, etc.) before it can be applied. AI must
  never bypass this.
- `AIAction.run()` must produce an `AIActionAuditRecord` (action type, input/output
  payloads, model name, whether guardrails passed) for every action — this is the audit
  trail requirement.
- AI calls must not happen inside a database transaction — dispatch long-running AI work
  as a Celery task instead.

### Background jobs

`app/tasks/celery_app.py` configures Celery against Redis (`CELERY_BROKER_URL`/
`CELERY_RESULT_BACKEND`) with `autodiscover_tasks(["app.tasks"])`; add new task modules
under `app/tasks/`.

### Configuration

`app/core/config.py` (`Settings`, pydantic-settings) reads all config from environment
variables / `.env` — see `backend/.env.example` for the full list (DB URL, Redis/Celery
URLs, CORS origins, AWS placeholders). Never hard-code secrets; production values come
from AWS Secrets Manager.

### Frontend structure

`frontend/src/features/<name>/` (organizations, stores, products, inventory, pricing,
devices, integrations) are still empty; `features/auth/` is implemented
(`AuthContext.jsx`, `api.js`, `tokenStorage.js`, `validation.js`, `options.js`) — each
feature's API calls, components, and hooks belong in its own folder, not scattered
across `components/` or duplicated per page. `App.jsx` wires the global providers in
order: `QueryClientProvider` (TanStack Query) → MUI `ThemeProvider` (`src/theme.js`) →
`AuthProvider` (`features/auth/AuthContext.jsx`) → `AppRouter`
(`src/routes/AppRouter.jsx`, React Router). `MainLayout` (`src/layouts/MainLayout.jsx`)
is the shared page chrome, showing `ProfileMenu` or a sign-in link depending on
`useAuth().isAuthenticated`. `src/api/client.js` is the single Axios instance (reads
`VITE_API_URL`) — do not create per-feature Axios instances; its interceptors attach the
access token, and on a 401 (outside `/auth/login|register|refresh`) transparently
refresh via `/auth/refresh` and retry once before giving up and clearing tokens.
`ProtectedRoute` (`src/routes/ProtectedRoute.jsx`) reads `useAuth().status` and redirects
to `/login` when not authenticated.

## Conventions carried over from the project charter

- Tenant isolation: every repository query touching tenant data must filter by
  `organization_id` (see `UserRepository`/`RoleRepository` for the pattern). This is a
  correctness requirement, not an optimization. Note `roles.organization_id` is
  nullable by design — `NULL` means a global system-role template (`is_system_role
  =True`), not "unscoped, skip the filter."
- API versioning: all new endpoints go under `/api/v1` via `app/api/v1/router.py`; do
  not add unversioned routes.
- RBAC: gate new endpoints with `Depends(require_permission(PermissionCode.X))`
  (`app/dependencies/auth.py`) rather than checking roles/permissions ad hoc in a route
  or service.
- New external integrations and ESL vendors must implement the `app/integrations/base.py`
  interfaces rather than being called ad hoc from services.
- New AI-driven features must go through `PricingGuardrail` and emit an
  `AIActionAuditRecord`, and must not run inside a DB transaction.

---

## Post-Clone Changes — Full Changelog

Everything below was added **after cloning from
`GlobalServicesAndSolutions/Pricing-Intelligence-Platform`** (merge-base: `81e4dff`,
Phases 0–15 already present). All work was done in bulk, not in isolated per-feature
commits.

---

### Product URL Fetcher

Lets a user paste a retailer product-page URL and have the create form pre-fill name,
price, brand, SKU, image, barcode, and other fields automatically.

**Backend:**
- `app/services/product_url_fetcher.py` — server-side HTML parser (`httpx`, 12 s timeout,
  browser-like User-Agent, `follow_redirects`). Reads `<title>`, OpenGraph meta tags, and
  `<script type="application/ld+json">` blocks. Extracts schema.org Product fields
  (`name`, `offers.price`, `brand.name`, `sku`, `gtin`, `image`) with OpenGraph fallback.
  A substantial-field heuristic (`_PRODUCT_SIGNAL_FIELDS`) ensures at least one of
  price/brand/sku/barcode/image is extracted — a bare `<title>` is not treated as product
  data. `url` is normalized (prepends `https://` when no scheme). Price is returned as a
  clean numeric string for direct form use. Known limit: no JS rendering; anti-bot sites
  (e.g. Akamai) may block the fetch.
- `POST /api/v1/products/fetch-from-url` — new endpoint gated behind `products.create`.
  Returns `ProductUrlSuggestion` (all fields `str | None` plus an `error` field). Never
  writes to the DB — the frontend pre-fills the form and the user reviews before Save.
  Failures return `error` with HTTP 200 so the UI can show a specific message.

**Product model — three new nullable columns** (migration `790934a4508d`):
- `product_url` (String 500) — the source retailer page.
- `qr_id` (String 150) — user-assigned or auto-generated identifier.
- `shelf_id` (String 150) — physical shelf number for shelf-label printing.

All three are nullable so existing rows and explicit `Product(...)` constructors in
`import_service.py` / `integration_apply_service.py` are unaffected.

**Schema additions** (`app/schemas/product.py`):
- `ProductUrlFetchRequest` — validated input for the fetch endpoint.
- `ProductUrlSuggestion` — output model (all optional fields plus `error`).

**Frontend:**
- `ProductForm.jsx` — "Product URL" TextField with a **Fetch** button; on click calls the
  endpoint and `setValue`-pre-fills every non-null suggestion field (including `product_url`),
  showing a success/"filled in N fields — review before saving" or error `Alert`.
- `features/products/api.js` — `fetchProductFromUrl` function.
- `features/products/hooks.js` — `useFetchProductFromUrl` hook.
- `features/products/validation.js` — three optional-string rules for the new fields.
- `ProductDetailsPage.jsx` — displays Product URL (as a clickable link), QR ID, and Shelf ID
  in the Basic Information section.

**Tests:**
- `tests/test_product_url_fetcher.py` — 6 unit tests (`httpx` mocked, no network):
  basic URL, OpenGraph fallback, JSON-LD extraction, missing product data returns error,
  URL normalization, field-specific extraction.

---

### QR Code Improvements

**QR now encodes `product_url`** instead of plain-text price card.
- When the product has a `product_url`, the QR encodes that URL (browser navigation on scan).
- When `product_url` is null, the QR encodes an empty string (valid blank QR image).
- Frontend label updated from "QR encodes:" to "QR link:" in `OutputJobsPage.jsx`.

**Shared QR renderer:** `app/outputs/qr_render.py`
- `render_qr_png(text, box_size, border, error_correction)` — produces QR PNG bytes.
- Used by both the standalone QR output adapter (`app/outputs/qr_code.py`) and the PDF label
  adapter, so the QR image on printed labels is identical to the standalone QR output.
- The `qr_code.py` adapter now delegates to `render_qr_png()` instead of inlining the
  `qrcode` library call. The inline `_ERROR_CORRECTION` dict was replaced with a tuple
  (`_ERROR_CORRECTION_LEVELS`) used only for validation.
- `OutputRenderContext` now carries the resolved product's `product_url`; the QR adapter reads
  `context.product.product_url` instead of re-querying the DB.

**Tests:**
- `test_qr_render.py` — shared renderer unit tests.
- `test_qr_full.py` (backend root) — manual smoke test that prints the QR link.

---

### PDF Label Redesign

Complete redesign of `app/outputs/pdf_label.py` from a loud red/yellow retail shelf-label to
a clean black-and-white three-column layout matching a real grocery price tag.

**Layout (three-column, configurable):**
- **Text column** — product name (Helvetica-Bold 9 pt), "RETAIL PRICE" sublabel (5.5 pt),
  large price (auto-sized to fit), SKU + brand at the bottom.
- **Unit price box** (center) — bordered rounded rectangle with "UNIT PRICE" header, the
  per-unit price (auto-sized to fit), and the unit suffix. Per-unit derived from product
  weight when available, otherwise "PER EA" (whole-product price / 1 each).
- **QR zone** (left or right) — embedded QR code via `render_qr_png()` with SKU text below.

**Configurable via output channel configuration:**
- `show_qr` (bool, default True) — show/hide the QR code.
- `qr_position` ("left" | "right", default "right") — QR on left or right side.
- `qr_size_mm` (int/float, default 18) — QR size in mm.
- `show_unit_price` (bool, default True) — show/hide the unit price box.
- `banner_position` ("top" | "bottom", default "bottom") — store-name banner at top or bottom.
- `banner_text` (str, optional) — store name override (falls back to `payload.store_name`).
- `label_width_mm` / `label_height_mm` (int/float, default 85 × 55) — label dimensions.

**Key layout details:**
- Badge (`product.shelf_id`): positioned opposite to banner — bottom-right when banner is top,
  centered below QR when banner is bottom. Extra 3 mm top padding on bottom-banner layout to
  prevent product name clipping.
- Unit price sizing: the `_unit_price_label()` static method derives per-unit from
  `product.weight` / `product.weight_unit` when both are set; falls back to "PER EA".
- Banner: store name centred in a filled rectangle with white Helvetica 10 pt text,
  truncated to fit.

**New validation:**
- `validate_configuration()` now checks `qr_position` ∈ {"left", "right"} and
  `banner_position` ∈ {"top", "bottom"}, raising `ValidationError` on invalid values.

**Config schema updated** (`_CONFIG_SCHEMA`): replaced the old `show_promo`/`label_size`/
`orientation`/`theme` keys with the new PDF-specific keys above.

**Palette**: replaced the old `_YELLOW`, `_RED`, `_DARK`, `_WHITE`, `_SEP` module-level
constants with a `_DEFAULT_COLORS` dict (7 hex color keys: background, border, text, banner,
unit_border, sublabel, placeholder) that can be overridden by a LabelTemplate.

**Tests:**
- `test_output_jobs.py::test_pdf_label_job_generates_pdf` — expanded: now uses
  `shelf_id="39"`, `product_url`, asserts `unit_suffix == "PER EA"`.
- `test_output_jobs.py::test_pdf_label_custom_format` — new: QR left, banner top, custom
  label size (90×60), weight-derived unit price (`6.48 / 2 qt = 3.24 PER QT`).
- `test_output_jobs.py::test_pdf_label_without_qr_or_unit_price` — new: both optional
  elements disabled, text-only label still renders.
- `test_output_channels.py::test_create_pdf_channel_accepts_format_configuration` — new.
- `test_output_channels.py::test_create_pdf_channel_rejects_unknown_qr_position` — new.
- `test_output_channels.py::test_create_pdf_channel_rejects_unknown_banner_position` — new.

---

### Label Template System (Stage 2)

A standalone org-scoped `LabelTemplate` entity that lets stores customize shelf-label colors
and background images without touching adapter code. Designed as the foundation for a future
full template builder (fonts, layout, spacing).

**Model:** `app/models/label_template.py`
- `LabelTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base)` — table `label_templates`.
- `organization_id` (UUID FK → organizations, indexed, NOT NULL).
- `name` (String 255).
- `colors` (JSON nullable) — dict of color key → 6-digit hex string.
- `background_image_url` (String 500 nullable) — opaque storage reference.

**Migration:** `a7f5c9e2b8d4`
- Creates `label_templates` table with PK, org FK, name, colors, background_image_url,
  created_at, updated_at.
- Adds `label_template_id` FK column to `output_channels` (nullable, `ON DELETE SET NULL`,
  indexed).

**FK on OutputChannel:** `app/models/output_channel.py`
- `label_template_id` (UUID nullable FK → label_templates, `SET NULL` on delete).
- NULL = built-in defaults (byte-identical to pre-template rendering).

**Repository:** `app/repositories/label_template_repository.py`
- `get_by_id_for_organization(template_id, org_id)` — scoped lookup.
- `list_by_organization(org_id)` — ordered by `created_at` descending.

**Service:** `app/services/label_template_service.py`
- Full CRUD: `create_template`, `get_template`, `list_templates`, `update_template`,
  `delete_template` (hard-delete; FK ON DELETE SET NULL detaches channels automatically).
- `upload_background_image`: validates extension whitelist (png/jpg/jpeg/gif/webp), enforces
  `max_import_file_size_mb`, stores via `get_storage_adapter().upload()`.

**Channel integration:** `app/services/output_channel_service.py`
- `_validate_label_template()` — checks template exists for the org on create/update.
- `create_channel` / `update_channel` set `channel.label_template_id` when present.

**Job service:** `app/services/output_job_service.py` → `_run()`
- Resolves the channel's template once at job start: fetches `template.colors` and
  `template.background_image_url` into `OutputRenderContext` fields
  (`template_colors`, `template_background_image_url`).
- Adapters stay DB-free — they read resolved values from the context only.

**OutputRenderContext** (`app/outputs/base.py`):
- Two new optional fields: `template_colors: dict[str, str] | None = None` and
  `template_background_image_url: str | None = None`.

**PDF adapter integration** (`app/outputs/pdf_label.py`):
- Merges `context.template_colors` over `_DEFAULT_COLORS` key-by-key; constructs
  `HexColor` palette from the merged dict.
- Background image: if `context.template_background_image_url` is set, downloads via
  `get_storage_adapter().download()` and draws behind all elements via `ImageReader`. Any
  failure (missing file, bad bytes, backend down) is caught with `logger.warning()` and the
  label renders on the plain color background — a job never fails for its decoration.

**Pydantic schemas:** `app/schemas/label_template.py`
- `LabelTemplateBase`: `name` (1–255 chars), `colors` (optional dict), `background_image_url`
  (optional, max 500). `colors` validated against `LABEL_COLOR_KEYS` allow-list (7 keys:
  background, border, text, banner, unit_border, sublabel, placeholder) and each value must
  match `^#[0-9a-fA-F]{6}$`.
- `LabelTemplateCreate`, `LabelTemplateUpdate`, `LabelTemplateOut`, `LabelTemplateListOut`.

**API:** `app/api/v1/label_templates.py`
- `GET /api/v1/outputs/label-templates` — list org templates (OUTPUTS_READ).
- `POST /api/v1/outputs/label-templates` — create (OUTPUTS_CREATE).
- `GET /api/v1/outputs/label-templates/{id}` — get (OUTPUTS_READ).
- `PUT /api/v1/outputs/label-templates/{id}` — update (OUTPUTS_UPDATE).
- `DELETE /api/v1/outputs/label-templates/{id}` — delete (OUTPUTS_UPDATE).
- `POST /api/v1/outputs/label-templates/{id}/background-image` — multipart upload (OUTPUTS_UPDATE).
- Router registered in `app/api/v1/router.py`.

**Frontend:**
- `LabelTemplateSelect.jsx` — dropdown with "None (defaults)" + existing templates + "Create
  new". Edit and Delete buttons per template. Uses CREATE_NEW sentinel to trigger inline
  editor.
- `LabelTemplateEditor.jsx` — template name field, 7 native color pickers (one per color key
  with labels), background image upload with preview and Remove button. Save/Cancel buttons.
  Supports both create (null template) and edit (existing template) modes.
- `ChannelForm.jsx` — `LabelTemplateSelect` + inline `LabelTemplateEditor` wired into the
  pdf_label section. Switches for `show_qr` and `show_unit_price`. Dropdowns for
  `qr_position` and `banner_position`. `qr_size_mm` text field. Delete-template confirmation
  dialog.
- `features/outputs/api.js` — `fetchLabelTemplates`, `fetchLabelTemplate`,
  `createLabelTemplate`, `updateLabelTemplate`, `deleteLabelTemplate`,
  `uploadTemplateBackgroundImage`.
- `features/outputs/hooks.js` — `useLabelTemplates`, `useCreateLabelTemplate`,
  `useUpdateLabelTemplate`, `useDeleteLabelTemplate`, `useUploadTemplateBackgroundImage`.
- `features/outputs/options.js` — `QR_POSITION_OPTIONS`, `BANNER_POSITION_OPTIONS`.
- `features/outputs/validation.js` — `label_template_id`, `show_qr`, `qr_position`,
  `qr_size_mm`, `show_unit_price`, `banner_position` schema fields.

**Tests:** `tests/test_label_templates.py` — 8 tests:
1. CRUD round-trip (create → get → update → list).
2. Tenant isolation (template not visible to another org).
3. Bad hex color rejection (422).
4. Background image upload roundtrip.
5. Channel template assignment validation (nonexistent template → 404).
6. PDF job with template colors renders correctly.
7. Delete template → channels fall back to defaults.
8. Unsupported image type rejection.

---

### Analytics Cache Fix

`app/services/analytics_service.py` — `_compute_from_snapshots` always recomputes today
on read (today's snapshot is never final — a price change / inventory adjustment / device
sync that landed moments ago must show up immediately). The Redis response cache (120 s TTL)
now covers **only settled day-ranges** that end strictly before today
(`cacheable_range = date_to < today`); anything spanning today bypasses the cache and
recomputes.

- Caught by `tests/test_analytics.py::test_price_change_count_and_average` (two back-to-back
  unfiltered dashboard reads; the second must reflect a just-made price change).
- Full suite at time of implementation: **314 passed, 0 failed**.

---

### Demo Data Seeding

`backend/seed_data.py` — re-seedable script that creates demo data for development:
- Creates demo organization(s) and assigns a system admin user.
- **Creates product categories (there were none before the clone).** Categories follow the
  existing self-referential hierarchy (`parent_id`). Parent categories are created first,
  then children. Skips duplicates (idempotent via `ensure_category`).
- Creates demo products with inventory, pricing rules, and price records per category.
- Run with `python seed_data.py` in `backend/`.

---

### Infrastructure

**`.gitignore` updated:**
- Added `.mcp.json` (MCP local project config).
- Added `.claude/` (Claude local statusline, settings, permissions — never on GitHub).
- Added `backend/var/` (local object-storage fallback used when `S3_BUCKET_NAME` is unset).

**Docker improvements:**
- `backend/entrypoint.sh` — new Docker entrypoint that runs `alembic upgrade head` (auto-migration on first run) then starts uvicorn.
- `backend/Dockerfile` — CMD changed from direct `uvicorn` to `./entrypoint.sh`. Added `chmod +x entrypoint.sh`.
- `README.md` — Docker setup instructions updated: added `alembic upgrade head` note for local dev, documented first-run auto-migration behavior, added `docker compose exec backend python seed_data.py` seeding command.

**Alembic migrations:**
- `790934a4508d` — adds `product_url`, `qr_id`, `shelf_id` nullable columns to `products`.
- `a7f5c9e2b8d4` — creates `label_templates` table; adds `label_template_id` FK column to
  `output_channels`.

**`README.md`** — updated with current project scope and setup instructions.

---

### ESL Integrations — Edit & Delete

The ESL Integrations list page (`/integrations`) previously had no row actions at all —
no way to change an integration's name/status/credentials or remove one once created.

**Backend:**
- `DELETE /api/v1/esl-integrations/{integration_id}` (`app/api/v1/esl_integrations.py`),
  gated by `PermissionCode.INTEGRATIONS_UPDATE` (same precedent as the Enterprise
  Integration Hub's field-mapping delete in `app/api/v1/integrations.py` — there's no
  dedicated delete permission for either integration domain).
- `esl_integration_service.delete_integration()` blocks deletion with a `ConflictError`
  (`code="esl_integration_has_devices"`) when any device still has
  `esl_integration_id` pointing at it — `devices.esl_integration_id` has a plain FK with
  no `ON DELETE SET NULL`, so an unguarded delete would otherwise surface as a raw DB
  constraint error. Same dependent-check precedent as `CategoryService.delete_category`.
- `DeviceRepository.count_by_esl_integration()` / `ESLIntegrationRepository.delete()` —
  the two repository methods the guard and delete need.
- Update (`PUT /esl-integrations/{id}`) already existed — no backend change needed there.

**Frontend:** `features/integrations/api.js`/`hooks.js` — `deleteIntegration`/
`useDeleteIntegration`. `IntegrationsListPage.jsx` originally grew an Edit-icon dialog and
a Delete-icon confirmation dialog per row; both were later folded into the Integration
Detail page (see the "ESL Devices Integration" section below) once that page existed.

**Tests:** the 10 existing `tests/test_esl_integrations.py` tests continued passing
unchanged; no new dedicated delete test was added in this pass (superseded by the
schema changes in the following section, which touch the same file).

---

### Full Responsive Redesign (Phone / Tablet / Desktop)

The entire frontend (57 pages) had zero mobile consideration: no `useMediaQuery` usage
anywhere, no `Drawer`/hamburger nav, 61 files rendering a MUI `Table` with no
column-priority or mobile fallback, and only 1 of 5 `Tabs` usages set `scrollable`. Redone
across every breakpoint using MUI's default breakpoints (xs/sm/md/lg/xl) as-is.

**Strategy — column-priority + native scroll** (chosen over a card-view rewrite so every
list stays a real, sortable MUI table): keep the primary identifier + status + actions
always visible; hide 1-4 lower-priority columns at `xs` (shown again at `sm+`); hide
tertiary metadata (cost/margin figures, timestamps) at `xs`+`sm` (shown at `md+`);
narrower in-tab tables (e.g. `features/integrationHub/*Table.jsx`) shift the threshold one
step (`sm`→`md`). Header/body `TableCell`s carry identical `sx={{ display: {...} }}` so
columns stay aligned when hidden.

**Navigation** (`frontend/src/layouts/MainLayout.jsx`, rewritten): a hamburger `IconButton`
+ `Drawer` (anchor="left") replaces the horizontal nav row below `md` (900px) — chosen over
`sm` because the nav row holds up to 5 items+dropdowns and clips well before 600px on a
real tablet. `useMediaQuery(theme.breakpoints.down("md"))` is used inline, deliberately
not wrapped in a custom hook (single call site). New `NavDrawerGroup` component
(`Collapse` + `ListItemButton`, not a `Menu` popover — the wrong idiom inside a vertical
drawer list) renders the same permission-gated `pricingMenuItems`/`aiMenuItems` arrays the
desktop `NavMenuButton` already used. The AppBar title collapses to "PIP" below `sm`.

**Tabs** (4 files): `variant="scrollable" scrollButtons="auto"` added to
`OutputJobsPage.jsx`, `AIPricingDashboardPage.jsx`, `DeviceDetailPage.jsx`,
`features/products/ProductForm.jsx` — a pure attribute add, matching
`IntegrationHubDetailPage.jsx`'s pre-existing usage.

**Tables** — column-hiding applied to 26 files: 21 `pages/*.jsx` (every top-level
`*ListPage.jsx` plus detail/dashboard pages with embedded tables — `ProductsListPage`,
`UsersListPage`, `InventoryDashboardPage` (10 columns, the widest table in the app), etc.)
and 5 `features/integrationHub/*Table.jsx` files. A handful of already-narrow tables
(`ImportWizardPage`, `PricingSimulationPage`, `LocationsTable.jsx`) needed only a
responsive `minWidth` fix, not column hiding.

**Filter bars**: fixed-px `minWidth` on filter `TextField`s (e.g. `sx={{ minWidth: 260 }}`)
converted to `sx={{ minWidth: { xs: "100%", sm: 260 } }}` across list pages so they don't
force horizontal overflow on phones; header `Stack`s use
`direction={{ xs: "column", sm: "row" }}`.

**Verification**: `npm run lint` (clean after every batch) and `npm run build` (clean,
314 modules, no new warnings). **No visual/browser-automation tool was available in this
environment** — verification was lint + build + code-reading (reasoning through the
breakpoint math per table), not a rendered screenshot or live device test. Manually check
on a real phone/tablet/resized browser before considering this fully validated.

---

### ESL Devices Integration — Merged Vendor-First Workflow

"ESL Integrations" (vendor connections) and "Devices" (registered hardware) were two
disconnected flat Settings entries; store was picked per-device or per-import-batch,
re-entered every time, and every devices table repeated Vendor/Store columns that are
really properties of which integration a device came from. Redone as one merged Settings
entry and a vendor-first workflow: create the vendor integration (including its store)
first, then discover/import/manage that vendor's devices underneath it.

**Data model**: `esl_integrations` gained a nullable `store_id` UUID FK → `stores.id`
(migration `7645d770b12a`, mirroring `OutputChannel.store_id`'s nullable-FK pattern) — one
integration now belongs to exactly one store. Nullable at the DB level for migration
safety; **required** one layer up by `ESLIntegrationCreate`.

**Backend:**
- `esl_integration_service.create_integration()`/`update_integration()` validate the store
  exists for the org (`StoreRepository.get_by_id_for_organization`, same check
  `device_service.create_device` already did) and set/update `integration.store_id`.
- `ImportDevicesRequest` dropped `store_id` — `import_devices()` now derives it from
  `integration.store_id` (raises `ConflictError(code="esl_integration_missing_store")` if
  unset, defensive since creation now requires one).
- `DeviceCreate` — `store_id`/`vendor_id` became optional; added `esl_integration_id:
  uuid.UUID | None`. A `model_validator` requires either `esl_integration_id`, or both
  `store_id` + `vendor_id` (the pre-existing manual/simulator path, unchanged).
  `device_service.create_device()` derives `store_id`/`vendor_id` from the integration
  (server-derived, never client-sent — same precedent as `import_devices`) when
  `esl_integration_id` is set.
- `DeviceOut`/`DeviceListParams`/`DeviceRepository.search()` — added `esl_integration_id`
  end-to-end, so devices can be listed scoped to one integration.
- Mechanical test updates: `tests/helpers.py::esl_integration_payload()` gained a required
  `store_id` kwarg; every call site in `tests/test_esl_integrations.py` creates a store
  first. Full suite: 366 passed, 1 skipped.

**Frontend:**
- **Settings nav** (`SettingsPage.jsx`): the "Devices" and "ESL Integrations" flat entries
  merged into one expandable "ESL Devices Integration" section (same `children` pattern as
  "Admin"/"Outputs") with "Vendor Integrations" (`/integrations`) and "All Devices"
  (`/devices`, kept as the manual/oversight path) children.
- **Setup wizard** (`IntegrationSetupWizardPage.jsx`) trimmed from 8 steps to 3 (Vendor +
  Store → Credentials → Test Connection) — Discover/Select-Store/Import/Assign/Test-Price
  moved to the new detail page below; "Finish" navigates to `/integrations/:id`.
- **New `IntegrationDetailPage.jsx`** (`/integrations/:integrationId`), tabbed like
  `IntegrationHubDetailPage.jsx`:
  - *Overview*: vendor/store/type/status/base URL, Test Connection, Edit (dialog, extended
    with a Store field), Delete.
  - *Devices*: table scoped to the integration via `useDevices({ eslIntegrationId })` —
    **no Vendor/Store columns**, since both are fixed and already shown once in Overview.
    Discover Devices + Import Selected (migrated from the old wizard steps), Add Device
    Manually (Device Name/Identifier/Model only — vendor/store implicit), and a per-device
    Test Price Update action (`useTestPriceUpdate`, restoring the old wizard step 8's
    Phase-9 `ESLIntegrationAdapter.push_price` coverage, distinct from the Phase-8
    simulator "Resync").
- `IntegrationsListPage.jsx` simplified: the Edit dialog moved to the detail page; the row
  action is now a "View" icon into `/integrations/:id` (Delete stays inline). Added a
  Store column.
- `DeviceForm.jsx`, `/devices/new`, `/devices/:id` (`DeviceDetailPage.jsx`), and
  `DevicesListPage.jsx`'s own Vendor/Store columns are unchanged — the manual path stays
  available exactly as before, and the global "All Devices" list is a cross-integration
  oversight view where those columns are the point, not duplication.

**Verification**: `ruff check`/`pytest -q` clean on the backend (366 passed, 1 skipped);
`npm run lint`/`npm run build` clean on the frontend. Same no-browser-tool caveat as the
responsive redesign above — click through the create-integration → detail-page →
discover/import/manual-add flow manually before treating it as fully validated.

---

### Device Delete

`DELETE /api/v1/devices/{device_id}` (`app/api/v1/devices.py`), gated by
`PermissionCode.DEVICES_MANAGE` (no dedicated `devices.delete` permission exists; MANAGE is
the stricter of the existing codes and already guards assignment/sync). Hard delete:
`device_service.delete_device()` first removes the device's `device_assignments` and
`device_sync_logs` (`delete_for_device()` on each repository — their FKs to `devices.id`
have no `ON DELETE CASCADE`, and that history is meaningless without the device), then the
device itself. The Phase-8 `ESLVendorAdapter` has no unregister call, so nothing is
notified vendor-side. Frontend: `deleteDevice`/`useDeleteDevice` in `features/devices/`,
plus a Delete icon and confirmation dialog on `DevicesListPage.jsx`. Tests: 3 new cases in
`tests/test_devices.py` (delete with assignment + sync log, cross-org 404, viewer 403).

---

### ESL Integrations list — Edit / Add Devices; Devices page layout

- `IntegrationsListPage.jsx` row actions are now View, **Add Devices**, **Edit**, Delete. The
  edit and add-device dialogs are shared components (`features/integrations/
  EditIntegrationDialog.jsx`, `AddDeviceDialog.jsx`) used by both the list page and
  `IntegrationDetailPage.jsx`.
- `AddDeviceDialog` mirrors the All Devices form (`DeviceForm.jsx`): Device Name, Vendor,
  Model, Device Identifier, Store, Status. Vendor and Store are shown **locked** to the
  integration's own values (the backend derives both from `esl_integration_id` regardless).
- **Per-device management inside the ESL Integration pages**: the device detail page's tab
  set (Overview with live ESL preview, Assigned Product + assignment history, Sync History
  with Resync, Device Health, Configuration) was extracted verbatim into
  `features/devices/DeviceManagementTabs.jsx` (`DeviceDetailPage.jsx` is now just a header
  around it), and `DeviceManageDialog.jsx` hosts it in a dialog. The integration detail
  Devices tab has a Manage (tune) action per device; adding a device — from the detail page
  or the list page's Add Devices action — opens the dialog on the new device automatically
  so a product can be assigned straight away.
- **Discover Devices fix** (`IntegrationDetailPage.jsx` Devices tab): the discover endpoint
  answers HTTP 200 with `success: false` + a reason when a vendor can't discover (Pricer
  missing its Plaza Store ID credential, Vusion/Hanshow/etc. stub adapters, unreachable
  host), and the UI used to discard that, so the button looked dead. It now shows the
  reason (with an "Edit integration" shortcut), an info notice for zero results, marks
  devices whose identifier is already registered org-wide as "Already added"
  (unselectable — identifiers are unique per organization), warns when the integration
  has no store, and `useImportDevices` now invalidates `["devices"]` so the table refreshes
  after an import.
- `DevicesListPage.jsx` table cut from 11 to 8 columns (Device+ID, Vendor/Model,
  Battery/Signal merged; Last Sync only at `lg+`) with wrapping text and an `xl` container,
  so it no longer scrolls horizontally.

---

*Post-clone changes documented by AbdulRehman, 2026-09-07. ESL Integration edit/delete,
full responsive redesign, and ESL Devices Integration merge documented 2026-09-17;
Device Delete 2026-09-18.*
