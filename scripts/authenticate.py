#!/usr/bin/env python3
"""Script to authenticate with Oura API and store OAuth tokens."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.oauth import OuraOAuth
from services.oura_client import OuraClient
from utils import logger
from utils.database import init_database


def main():
    """Run OAuth authentication flow."""
    print("\n" + "="*80)
    print("OURA API AUTHENTICATION SETUP")
    print("="*80 + "\n")
    
    # Initialize database
    print("Initializing database...")
    try:
        init_database()
        print("✓ Database initialized\n")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}\n")
        return
    
    # Start OAuth flow
    oauth = OuraOAuth()

    try:
        # Get authorization code and state
        auth_code, state = oauth.start_auth_flow()

        if not auth_code:
            print("\n✗ No authorization code provided. Exiting.")
            return

        # Exchange code for tokens (with state verification for CSRF protection)
        print("\nExchanging authorization code for tokens...")
        token_data = oauth.exchange_code_for_token(auth_code, state)

        # Save token temporarily with "temp" user_id
        oauth.save_token("temp", token_data)

        # Get user ID from personal info endpoint
        print("Fetching user information...")
        client = OuraClient("temp")
        personal_info = client.get_personal_info()
        user_id = personal_info.get("id")
        
        if not user_id:
            print("\n✗ Could not retrieve user ID. Exiting.")
            return
        
        # Save token with correct user ID
        oauth.save_token(user_id, token_data)
        
        print("\n" + "="*80)
        print("✓ AUTHENTICATION SUCCESSFUL!")
        print("="*80)
        print(f"\nUser ID: {user_id}")
        print(f"Access Token: {token_data['access_token'][:20]}...")
        print(f"Scopes: {token_data.get('scope', 'N/A')}")
        print("\nYou can now run the data sync script:")
        print("  python scripts/sync_data.py\n")
        
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
        logger.exception("Authentication error")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)