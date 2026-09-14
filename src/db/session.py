"""Database session and connection management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config.config import config
from src.db.models import Base
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    config.data.database_url,
    connect_args={"check_same_thread": False} if 'sqlite' in config.data.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
