"""Database connection and session management."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models.base import Base
from utils import logger


# Create engine
_engine = None
_SessionLocal = None


def get_engine():
    """
    Get or create the database engine.

    Returns:
        SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        database_url = settings.database_url_constructed
        _engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10
        )
        logger.info(f"Database engine created for: {database_url.split('@')[-1]}")
    return _engine


def get_session_factory():
    """
    Get or create the session factory.

    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        logger.debug("Session factory created")
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session as a context manager.

    Usage:
        with get_db() as db:
            user = db.query(User).first()
            db.add(new_obj)
            # Session automatically commits on exit

    Yields:
        SQLAlchemy Session instance
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
        logger.debug("Database session committed")
    except Exception as e:
        db.rollback()
        logger.error(f"Database session rolled back due to error: {e}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def init_database():
    """
    Initialize the database by creating all tables.

    This creates all tables defined in SQLAlchemy models that inherit from Base.
    """
    try:
        engine = get_engine()

        # Import all models to ensure they're registered with Base
        # This is necessary for Base.metadata.create_all() to work
        from models.auth import OAuthToken
        from models.daily_activity import DailyActivity
        from models.daily_cardiovascular_age import DailyCardiovascularAge
        from models.daily_readiness import DailyReadiness
        from models.daily_resilience import DailyResilience
        from models.daily_sleep import DailySleep
        from models.daily_spo2 import DailySpo2
        from models.daily_stress import DailyStress
        from models.enhanced_tag import EnhancedTag
        from models.heart_rate import HeartRate
        from models.personal_info import PersonalInfo
        from models.rest_mode_period import RestModePeriod
        from models.ring_configuration import RingConfiguration
        from models.session import Session as SessionModel
        from models.sleep import Sleep
        from models.sleep_time import SleepTime
        from models.tag import Tag
        from models.vo2_max import VO2Max
        from models.workout import Workout

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def drop_all_tables():
    """
    Drop all tables from the database.

    WARNING: This will delete all data! Use with caution.
    """
    try:
        engine = get_engine()

        # Import all models to ensure they're registered with Base
        from models.auth import OAuthToken
        from models.daily_activity import DailyActivity
        from models.daily_cardiovascular_age import DailyCardiovascularAge
        from models.daily_readiness import DailyReadiness
        from models.daily_resilience import DailyResilience
        from models.daily_sleep import DailySleep
        from models.daily_spo2 import DailySpo2
        from models.daily_stress import DailyStress
        from models.enhanced_tag import EnhancedTag
        from models.heart_rate import HeartRate
        from models.personal_info import PersonalInfo
        from models.rest_mode_period import RestModePeriod
        from models.ring_configuration import RingConfiguration
        from models.session import Session as SessionModel
        from models.sleep import Sleep
        from models.sleep_time import SleepTime
        from models.tag import Tag
        from models.vo2_max import VO2Max
        from models.workout import Workout

        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped")

    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


def reset_database():
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data! Use with caution.
    """
    try:
        logger.warning("Resetting database - all data will be lost!")
        drop_all_tables()
        init_database()
        logger.info("Database reset complete")
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise
