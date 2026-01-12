"""Database configuration and SQLAlchemy setup for PostgreSQL backend.

Provides:
- Engine and session management
- Connection pooling configuration
- Base ORM class for all models
- Transaction context managers
- Health check and initialization
"""

from typing import Optional, Generator
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Base class for all ORM models
Base = declarative_base()


class DatabaseConfig:
    """Database configuration from environment."""
    
    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600
    ):
        """Initialize database configuration.
        
        Args:
            database_url: PostgreSQL connection string
            echo: Log SQL statements
            pool_size: Number of connections to maintain
            max_overflow: Max overflow connections
            pool_pre_ping: Test connections before use
            pool_recycle: Recycle connections after seconds
        """
        self.database_url = database_url
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_pre_ping = pool_pre_ping
        self.pool_recycle = pool_recycle


class DatabaseEngine:
    """SQLAlchemy engine and session management."""
    
    _instance: Optional['DatabaseEngine'] = None
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database engine.
        
        Args:
            config: DatabaseConfig instance
        """
        self.config = config
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        logger.info(f"✓ Database engine initialized: {config.database_url}")
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with pooling."""
        engine = create_engine(
            self.config.database_url,
            echo=self.config.echo,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=self.config.pool_pre_ping,
            pool_recycle=self.config.pool_recycle
        )
        
        # Log pool events for debugging
        @event.listens_for(engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug(f"Database connection opened: {id(dbapi_conn)}")
        
        @event.listens_for(engine, "close")
        def receive_close(dbapi_conn, connection_record):
            logger.debug(f"Database connection closed: {id(dbapi_conn)}")
        
        return engine
    
    @classmethod
    def init(cls, config: DatabaseConfig) -> 'DatabaseEngine':
        """Initialize singleton instance.
        
        Args:
            config: DatabaseConfig
            
        Returns:
            DatabaseEngine instance
        """
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'DatabaseEngine':
        """Get singleton instance.
        
        Returns:
            DatabaseEngine instance (must call init first)
        """
        if cls._instance is None:
            raise RuntimeError("DatabaseEngine not initialized. Call init() first.")
        return cls._instance
    
    def get_session(self) -> Session:
        """Get new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
    
    @contextmanager
    def session_context(self) -> Generator[Session, None, None]:
        """Context manager for database sessions.
        
        Yields:
            SQLAlchemy session with automatic cleanup
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity.
        
        Returns:
            True if database is accessible
        """
        try:
            with self.session_context() as session:
                session.execute("SELECT 1")
                logger.info("✓ Database health check passed")
                return True
        except Exception as e:
            logger.error(f"✗ Database health check failed: {e}")
            return False
    
    def create_tables(self):
        """Create all tables defined in Base.metadata.
        
        Useful for development/testing.
        """
        Base.metadata.create_all(bind=self.engine)
        logger.info("✓ Database tables created")
    
    def drop_tables(self):
        """Drop all tables defined in Base.metadata.
        
        WARNING: Destructive operation.
        """
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("⚠️ All database tables dropped")
    
    def close(self):
        """Close all database connections."""
        self.engine.dispose()
        logger.info("✓ Database connections closed")


# Dependency for FastAPI routes
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session.
    
    Usage in routes:
        @app.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        SQLAlchemy session
    """
    db = DatabaseEngine.get_instance().get_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
