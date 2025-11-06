#!/usr/bin/env python3
"""Script to initialize the database."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import init_database, drop_all_tables
from utils import logger


def main():
    """Initialize database tables."""
    print("\n" + "="*80)
    print("DATABASE INITIALIZATION")
    print("="*80 + "\n")
    
    # Ask for confirmation if dropping tables
    if "--drop" in sys.argv:
        response = input("⚠️  This will DROP ALL TABLES. Are you sure? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return 0
        
        print("\nDropping all tables...")
        try:
            drop_all_tables()
            print("✓ All tables dropped\n")
        except Exception as e:
            print(f"✗ Failed to drop tables: {e}")
            logger.exception("Drop tables error")
            return 1
    
    # Create tables
    print("Creating database tables...")
    try:
        init_database()
        print("\n✓ Database tables created successfully!")
        print("\nNext steps:")
        print("1. Run: python scripts/authenticate.py")
        print("2. Run: python scripts/sync_data.py\n")
    except Exception as e:
        print(f"\n✗ Failed to create tables: {e}")
        logger.exception("Database initialization error")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)