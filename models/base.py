"""
Clase base declarativa de SQLAlchemy para todos los modelos.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base para todos los modelos ORM de HealthTrack Pro."""
    pass
