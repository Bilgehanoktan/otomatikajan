"""
Sovereign AGI — libs/db/base.py
Core database base class and SQL primitives.
Created to break circular dependencies between models and session.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import JSON as SA_JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.types import TypeDecorator

class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base."""
    pass

def utcnow():
    """Returns the current UTC time."""
    return datetime.now(timezone.utc)

def SmartJSON():
    """Returns JSONB for Postgres and JSON for other databases (SQLite)."""
    return PG_JSONB().with_variant(SA_JSON(), "sqlite")

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses String(32).
    """
    impl = PG_UUID
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(SA_JSON()) # Fallback for non-PG testing
