# PostgreSQL Migration Notes (Aiven Free — PoC only)

This is a temporary adaptation for Aiven PostgreSQL (free tier) to support the PoC/demo. Production will revert to MySQL (Hostinger or Aiven MySQL).

## Key adjustments made for PostgreSQL compatibility:
1. `JSON` columns: SQLAlchemy `JSON` is compatible with PostgreSQL natively (`JSONB` support optional, `JSON` works). No code change needed.
2. `Numeric(15, 4)` -> PostgreSQL supports `Numeric(15, 4)` natively.
3. Enum columns (`Enum(native_enum=False)`) -> PostgreSQL uses text types; `native_enum=False` is required, which is already set.
4. UUID primary keys (`Uuid(as_uuid=True)`) -> PostgreSQL supports UUID natively via `Uuid` type.
5. Migration chain (`30+ migrations`): Must be regenerated/re-run on a fresh PostgreSQL DB for PoC. This file does NOT replace Alembic; it documents the manual process.

## Manual PoC Setup (for Aiven PostgreSQL):
1. Create Aiven PostgreSQL instance.
2. Update `backend/.env`: set `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, etc. to the Aiven endpoint. Note: the driver in `config.py` uses `mysql+pymysql`. For PostgreSQL, change to `postgresql+psycopg2` and install `psycopg2-binary`.
3. Re-run `alembic upgrade head` against the Aiven DB.
4. Run `python seed_data.py` to populate demo data.

NOTE: This is a PoC-only file. Production (Hostinger) will revert to MySQL with `mysql+pymysql`; no long-term PostgreSQL migration is intended.
