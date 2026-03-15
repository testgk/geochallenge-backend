"""
Base entity class for all database entities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class BaseEntity(ABC):
    """
    Abstract base class for all database entities.
    Provides common fields and methods for entity management.
    """
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """Create entity from dictionary."""
        pass

    @classmethod
    @abstractmethod
    def table_name(cls) -> str:
        """Return the database table name for this entity."""
        pass

    def is_persisted(self) -> bool:
        """Check if entity has been saved to database."""
        return self.id is not None
