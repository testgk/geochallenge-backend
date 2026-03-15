"""
User model and repository for database operations.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import bcrypt

from db.connection import get_db_connection


@dataclass
class User:
    """User data model."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))


class UserRepository:
    """Repository for User database operations."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create(self, username: str, email: str, password: str) -> User:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            
        Returns:
            Created User object
        """
        password_hash = User.hash_password(password)
        
        query = """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, password_hash, created_at, updated_at, is_active
        """
        
        result = self.db.execute_one(query, (username, email, password_hash))
        return self._row_to_user(result) if result is not None else None
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by their ID."""
        query = "SELECT * FROM users WHERE id = %s"
        result = self.db.execute_one(query, (user_id,))
        return self._row_to_user(result) if result else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username."""
        query = "SELECT * FROM users WHERE username = %s"
        result = self.db.execute_one(query, (username,))
        return self._row_to_user(result) if result else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email."""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.db.execute_one(query, (email,))
        return self._row_to_user(result) if result else None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination."""
        query = "SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s"
        results = self.db.execute(query, (limit, offset))
        return [self._row_to_user(row) for row in results]
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Update a user's fields.
        
        Args:
            user_id: ID of user to update
            **kwargs: Fields to update (username, email, is_active)
        """
        allowed_fields = {'username', 'email', 'is_active'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return self.get_by_id(user_id)
        
        set_clause = ", ".join([f"{k} = %s" for k in update_fields.keys()])
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        values = list(update_fields.values()) + [user_id]
        
        query = f"""
            UPDATE users 
            SET {set_clause}
            WHERE id = %s
            RETURNING id, username, email, password_hash, created_at, updated_at, is_active
        """
        
        result = self.db.execute_one(query, tuple(values))
        return self._row_to_user(result) if result else None
    
    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update a user's password."""
        password_hash = User.hash_password(new_password)
        
        query = """
            UPDATE users 
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        
        self.db.execute(query, (password_hash, user_id))
        return True
    
    def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        query = "DELETE FROM users WHERE id = %s"
        self.db.execute(query, (user_id,))
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password.
        
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.get_by_username(username)
        if user and user.verify_password(password):
            return user
        return None
    
    @staticmethod
    def _row_to_user(row: dict) -> User:
        """Convert a database row to a User object."""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_active=row['is_active']
        )
