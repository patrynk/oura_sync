#!/usr/bin/env python3
"""Script to sync Oura data to database."""
import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.oura_client import OuraClient
from services.oauth import OuraOAuth
from models.auth import OAuthToken
from models.personal_info import PersonalInfo
from utils import logger, get_db


def get_user_id() -> str:
    """Get the user ID from database."""
    with get_db() as db:
        token = db.query(OAuthToken).first()
        if not token:
            print("No authentication found. Please run: python scripts/authenticate.py")
            sys.exit(1)
        return token.user_id


def sync_personal_info(client: OuraClient, user_id: str):
    """Sync personal information."""
    logger.info("Syncing personal info...")
    try:
        data = client.get_personal_info()
        
        with get_db() as db:
            existing = db.query(PersonalInfo).filter(PersonalInfo.id == data["id"]).first()
            
            if existing:
                for key, value in data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                logger.info("Updated personal info")
            else:
                personal_info = PersonalInfo(
                    id=data["id"],
                    user_id=user_id,
                    age=data.get("age"),
                    weight=data.get("weight"),
                    height=data.get("height"),
                    biological_sex=data.get("biological_sex"),
                    email=data.get("email")
                )
                db.add(personal_info)
                logger.info("Created personal info record")
        
        return True
    except Exception as e:
        logger.error(f"Failed to sync personal info: {e}")
        return False


def sync_daily_data(client: OuraClient, user_id: str, start_date: str, end_date: str, data_types: list):
    """Sync daily summary data."""
    methods_map = {
        "daily_activity": client.get_daily_activity,
        "daily_sleep": client.get_daily_sleep,
        "daily_readiness": client.get_daily_readiness,
        "daily_spo2": client.get_daily_spo2,
        "daily_stress": client.get_daily_stress,
        "daily_resilience": client.get_daily_resilience,
        "daily_cardiovascular_age": client.get_daily_cardiovascular_age,
    }
    
    for data_type in data_types:
        if data_type not in methods_map:
            continue
        
        logger.info(f"Syncing {data_type}...")
        try:
            method = methods_map[data_type]
            data_list = method(start_date, end_date)
            
            # For now, just log the data
            # In production, you'd save to database
            logger.info(f"Retrieved {len(data_list)} {data_type} records")
            
            # Save to JSON file for reference
            output_dir = Path(__file__).parent.parent / "data" / data_type
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{start_date}_to_{end_date}.json"
            with open(output_file, "w") as f:
                json.dump(data_list, f, indent=2, default=str)
            
            logger.info(f"Saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to sync {data_type}: {e}")


def main():
    """Main sync function."""
    parser = argparse.ArgumentParser(description="Sync Oura Ring data to database")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--initial", action="store_true", help="Initial sync (90 days)")
    parser.add_argument("--types", help="Comma-separated data types to sync")
    parser.add_argument("--all", action="store_true", help="Sync all data types")
    parser.add_argument("--sync-personal-info", action="store_true", help="Sync personal info (only needed once)")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("OURA DATA SYNC")
    print("="*80 + "\n")
    
    # Get user ID
    user_id = get_user_id()
    logger.info(f"Syncing data for user: {user_id}")
    
    # Create client
    client = OuraClient(user_id)
    
    # Determine date range
    if args.initial:
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
    else:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date() if args.end_date else date.today()
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date() if args.start_date else end_date - timedelta(days=7)
    
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    logger.info(f"Date range: {start_date_str} to {end_date_str}")

    # Sync personal info if requested
    if args.sync_personal_info:
        logger.info("Syncing personal info...")
        sync_personal_info(client, user_id)
    
    # Determine data types to sync
    if args.all:
        data_types = [
            "daily_activity", "daily_sleep", "daily_readiness",
            "daily_spo2", "daily_stress", "daily_resilience",
            "daily_cardiovascular_age"
        ]
    elif args.types:
        data_types = [t.strip() for t in args.types.split(",")]
    else:
        # Default: sync main daily summaries
        data_types = ["daily_activity", "daily_sleep", "daily_readiness"]
    
    logger.info(f"Syncing data types: {', '.join(data_types)}")
    
    # Sync data
    sync_daily_data(client, user_id, start_date_str, end_date_str, data_types)
    
    print("\n" + "="*80)
    print("✓ SYNC COMPLETE")
    print("="*80)
    print(f"\nSynced {len(data_types)} data types")
    print(f"Date range: {start_date_str} to {end_date_str}")
    print("\nData files saved to: ./data/\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)