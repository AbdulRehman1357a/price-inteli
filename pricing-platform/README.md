# Retail Pricing Intelligence Platform

Multi-tenant B2B SaaS platform for retail pricing intelligence: products, inventory,
pricing rules, promotions, multi-store management, ESL devices, ERP/POS integrations,
output channels, and AI pricing recommendations.

**Phase 10 complete**: multi-tenancy, JWT auth, RBAC (6 system roles / 39 permissions), a
minimal user-management foundation, Store Management, Category/Product Management,
Multi-store Inventory Management, Product/Inventory Bulk Import (CSV/XLSX upload,
column-mapping wizard, background processing, per-row error reporting), a deterministic
Pricing Engine (prices, price history, pricing rules with 10 rule types/5 constraint
types, a rule builder UI, and a rule test/preview mode), an Output Orchestration Engine
(output channels and jobs across 4 output types — ESL simulator, QR code, printable PDF
label, public web price display — with job monitoring and retry), an ESL Device
Platform Foundation (a vendor-agnostic device catalog/adapter interface, MQTT-based
device sync with a simulated acknowledgement, product-to-device assignment, sync
history, device health, and Device Management UI with a device detail page), a
Third-Party ESL Integration Framework (an async vendor plugin architecture with
encrypted-at-rest credentials, a Mock adapter and a real-when-reachable MQTT adapter,
placeholder adapters for five named vendors that fail honestly rather than faking a
connection, a real Pricer Plaza API integration (with OAuth2 token auth, device discovery,
price push, a standalone local simulator for end-to-end testing, and vendor-aware credential
fields in the integration wizard), and an 8-step Integration Setup Wizard covering vendor
selection through a test price push), an Enterprise Integration Hub (a canonical retail data model —
CanonicalProduct/Price/Inventory/Promotion/Store — that CSV/REST API/Webhook adapters
map external records into via configurable field mappings and transformations, applied
into real Product/Price/Inventory/Store data by Celery-backed background sync jobs with
retry, plus placeholder SAP/Oracle providers), and a Product URL Fetcher (see below)
are implemented. Real third-party vendor
API/SDK access (both ESL and ERP/POS), physical ESL hardware, and AI are not
implemented yet.

Bulk import, output jobs, and Enterprise Integration Hub sync jobs need Redis + a Celery
worker to actually process queued jobs in the background (`docker compose up` in
`infrastructure/`, or run Redis locally and
`celery -A app.tasks.celery_app worker --loglevel=info` from `backend/`) — without one,
uploaded imports and dispatched output/sync jobs stay `queued`/`pending`. File storage falls
back to a local `backend/var/storage/` directory when `S3_BUCKET_NAME` is unset, so
imports still work end-to-end without real AWS infrastructure. Device syncs and MQTT
ESL integrations work the same way without a running MQTT broker — the relevant
adapters always simulate (or honestly report the failed) acknowledgement synchronously;
publishing to the `mqtt` service in `infrastructure/docker-compose.yml` (not started by
default) is best-effort on top. ESL integration credentials are encrypted with a Fernet
key (`ESL_CREDENTIALS_ENCRYPTION_KEY`) that, like `JWT_SECRET_KEY`, has an insecure
dev-only default and must be overridden via AWS Secrets Manager in production.

Product URL Fetcher (`backend/app/services/product_url_fetcher.py`,
`POST /api/v1/products/fetch-from-url`): pastes a retailer product page URL (e.g. a
Walmart item page) and returns structured data extracted from the page's OpenGraph meta
tags and schema.org JSON-LD — name, price, currency, brand, SKU, barcode/GTIN, image,
and description — so the person at the POS doesn't type every product by hand. The
endpoint is read-only (never writes to the database); the React form pre-fills the
returned fields for review before Save. Three new nullable columns were added to
`products`: `product_url` (the source page URL), `qr_id`, and `shelf_id` — all optional
so existing products and bulk imports are unaffected. Extraction is best-effort by
design: sites that embed structured server-side data (Walmart, Amazon, most major
retailers) yield good results; sites that render everything client-side may return
nothing, and anti-bot protection (Akamai/Cloudflare) may block the server-side fetch
entirely — in those cases the UI shows a clear error and the user fills fields manually.
No new parsing dependencies were added (Python's stdlib `html.parser` handles the
extraction); `httpx` (already in the dependency list) handles the HTTP fetch.

## Architecture

Modular monolith. See `backend/app/` for the layering:

```
routes (app/api/v1) → services (app/services) → repositories (app/repositories) → db
```

- `app/models/mixins.py` — shared UUID PK / UTC timestamp / soft-delete / audit mixins
  every domain model composes with.
- `app/integrations/base.py` — adapter interface every ERP/POS/output-channel and ESL
  vendor integration must implement.
- `app/ai/base.py` — every AI-driven pricing action must produce an audit record and
  pass through a deterministic `PricingGuardrail` before it can take effect.

## Stack

- **Frontend**: React + Vite + Material UI + React Router + TanStack Query + Axios +
  React Hook Form + Zod
- **Backend**: Python + FastAPI + SQLAlchemy + Alembic + Pydantic + Celery
- **Database**: MySQL 8
- **Infra**: Docker, Redis, MQTT (ESL), AWS (RDS / S3 / Secrets Manager / CloudWatch)

## Getting started (local dev)

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head        # apply all migrations (first run creates schema + seeds)
uvicorn app.main:app --reload
```

API available at `http://localhost:8000/api/v1/health`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App available at `http://localhost:5173`.

### Full stack via Docker Compose

```bash
cd pricing-platform
cp backend/.env.example backend/.env   # required — Docker reads this file
cd infrastructure
docker compose up --build
```

On first run the backend container automatically:
1. Runs all Alembic migrations (`alembic upgrade head`)
2. Starts the API server

The database will have the schema and seeded roles/permissions, but no demo
products/stores. To seed demo data:

```bash
docker compose exec backend python seed_data.py
```

### Database migrations

Migrations are managed with Alembic (`backend/alembic/versions/`). When running
locally (not Docker), apply them manually:

```bash
cd backend
alembic revision --autogenerate -m "add <table>"
alembic upgrade head
```

Auto-creation of tables (`Base.metadata.create_all`) is never used outside tests —
production schema changes always go through Alembic migrations.

## Tests

```bash
cd backend
pytest
```
