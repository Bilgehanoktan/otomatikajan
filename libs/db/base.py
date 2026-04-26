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
from sqlalchemy.types import TypeDecorator, CHAR

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
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            try:
                value = uuid.UUID(value)
            except (ValueError, TypeError):
                return value
        
        if dialect.name == "postgresql":
            return value
        else:
            return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            # Ensure it is a string for processing
            val_str = str(value).replace("-", "")
            try:
                # If it has 32 chars, it's a valid hex UUID
                if len(val_str) == 32:
                    return uuid.UUID(hex=val_str)
                # Fallback to standard constructor
                return uuid.UUID(str(value))
            except (ValueError, TypeError):
                # If all else fails, return as is or log (but don't crash)
                return value
        return value
