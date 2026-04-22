"""SQLAlchemy declarative base for module-level schema models.

Each module owns its DB tables and extends this base.  A CI linter checks
that no module imports another's ``repository.py`` or ``models.py``.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all module models."""
