"""
User entity for database representation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from entities.base import BaseEntity


@dataclass
class UserEntity(BaseEntity):
    """
    User entity representing a player in the system.
    Maps to the 'users' table in the database.
    """
    username: str = ""
    email: str = ""
    password_hash: str = ""
    is_active: bool = True
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    total_score: int = 0
    games_played: int = 0

    @classmethod
    def table_name(cls) -> str:
        return "users"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'is_active': self.is_active,
            'display_name': self.display_name,
            'avatar_url': self.avatar_url,
            'total_score': self.total_score,
            'games_played': self.games_played,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserEntity':
        return cls(
            id=data.get('id'),
            username=data.get('username', ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            is_active=data.get('is_active', True),
            display_name=data.get('display_name'),
            avatar_url=data.get('avatar_url'),
            total_score=data.get('total_score', 0),
            games_played=data.get('games_played', 0),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def __repr__(self) -> str:
        return f"UserEntity(id={self.id}, username='{self.username}', email='{self.email}')"
