from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model.

    Alembic's env.py imports Base.metadata as the migration autogenerate
    target, so every model module must be imported wherever this Base is
    used before running `alembic revision --autogenerate`.
    """
