"""
PostgreSQL database connection management.
"""

import os
from contextlib import contextmanager
from typing import Optional, Generator
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor


class DatabaseConfig:
    """Database configuration from environment variables."""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.database = os.getenv('DB_NAME', 'geochallenge_db')
        self.user = os.getenv('DB_USER', 'geochallenge')
        self.password = os.getenv('DB_PASSWORD', 'geochallenge_secret')
        self.min_connections = int(os.getenv('DB_MIN_CONNECTIONS', '1'))
        self.max_connections = int(os.getenv('DB_MAX_CONNECTIONS', '10'))

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseConnection:
    """
    Manages PostgreSQL database connections using a connection pool.
    
    Usage:
        db = DatabaseConnection()
        db.connect()
        
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
        
        db.close()
    """
    
    _instance: Optional['DatabaseConnection'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.config = DatabaseConfig()
    
    def connect(self) -> None:
        """Initialize the connection pool."""
        if self._pool is None:
            try:
                self._pool = pool.ThreadedConnectionPool(
                    minconn=self.config.min_connections,
                    maxconn=self.config.max_connections,
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.user,
                    password=self.config.password
                )
                print(f"Connected to PostgreSQL database at {self.config.host}:{self.config.port}")
            except psycopg2.Error as e:
                print(f"Failed to connect to database: {e}")
                raise
    
    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None
            print("Database connection pool closed")
    
    @contextmanager
    def get_connection(self) -> Generator:
        """Get a connection from the pool."""
        if self._pool is None:
            self.connect()
        
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = True) -> Generator:
        """
        Get a cursor for executing queries.
        
        Args:
            dict_cursor: If True, returns results as dictionaries
        """
        cursor_factory = RealDictCursor if dict_cursor else None
        
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute(self, query: str, params: tuple = None) -> list:
        """Execute a query and return all results."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if cursor.description:
                return cursor.fetchall()
            return []
    
    def execute_one(self, query: str, params: tuple = None) -> Optional[dict]:
        """Execute a query and return a single result."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            if cursor.description:
                return cursor.fetchone()
            return None
    
    def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() is not None
        except Exception:
            return False


# Global singleton instance
_db_instance: Optional[DatabaseConnection] = None


def get_db_connection() -> DatabaseConnection:
    """Get the global database connection instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance
