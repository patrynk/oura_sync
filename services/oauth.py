"""OAuth2 authentication service for Oura API."""
import webbrowser
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import requests
from requests.auth import HTTPBasicAuth

from config import settings
from models.auth import OAuthToken
from utils import logger
from utils.database import get_db


class OuraOAuth:
    """Handle OAuth2 authentication flow with Oura API."""
    
    def __init__(self):
        self.client_id = settings.oura_client_id
        self.client_secret = settings.oura_client_secret
        self.redirect_uri = settings.oura_redirect_uri
        self.auth_url = f"{settings.oura_auth_base_url}/authorize"
        self.token_url = f"{settings.oura_auth_base_url}/token"
        
    def get_authorization_url(self) -> str:
        """
        Generate the authorization URL for user consent.
        
        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(settings.oauth_scopes)
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        logger.info(f"Authorization URL generated")
        return auth_url
    
    def start_auth_flow(self) -> str:
        """
        Start the OAuth flow by opening browser and getting authorization code.
        
        Returns:
            Authorization code
        """
        auth_url = self.get_authorization_url()
        
        print("\n" + "="*80)
        print("OURA API AUTHORIZATION")
        print("="*80)
        print(f"\nPlease visit this URL to authorize the application:\n")
        print(f"{auth_url}\n")
        print("Opening browser automatically...")
        print("="*80 + "\n")
        
        # Open browser
        webbrowser.open(auth_url)
        
        # Get authorization code from user
        auth_code = input("Enter the authorization code from the redirect URL: ").strip()
        
        return auth_code
    
    def exchange_code_for_token(self, auth_code: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            auth_code: Authorization code from OAuth callback
            
        Returns:
            Token response dictionary
        """
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(
            self.token_url,
            data=data,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise Exception(f"Failed to exchange code for token: {response.text}")
        
        tokens = response.json()
        logger.info("Successfully exchanged authorization code for tokens")
        return tokens
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response dictionary
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(
            self.token_url,
            data=data,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise Exception(f"Failed to refresh token: {response.text}")
        
        tokens = response.json()
        logger.info("Successfully refreshed access token")
        return tokens
    
    def save_token(self, user_id: str, token_data: dict):
        """
        Save OAuth token to database.
        
        Args:
            user_id: User identifier
            token_data: Token response from Oura API
        """
        with get_db() as db:
            # Calculate token expiration
            expires_in = token_data.get("expires_in", 86400)  # Default 24 hours
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            # Check if token exists
            existing_token = db.query(OAuthToken).filter(
                OAuthToken.user_id == user_id
            ).first()
            
            if existing_token:
                # Update existing token
                existing_token.access_token = token_data["access_token"]
                existing_token.refresh_token = token_data["refresh_token"]
                existing_token.token_type = token_data.get("token_type", "Bearer")
                existing_token.expires_at = expires_at
                existing_token.scopes = token_data.get("scope", "")
                logger.info(f"Updated OAuth token for user {user_id}")
            else:
                # Create new token
                token = OAuthToken(
                    user_id=user_id,
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_at=expires_at,
                    scopes=token_data.get("scope", "")
                )
                db.add(token)
                logger.info(f"Saved new OAuth token for user {user_id}")
    
    def get_token(self, user_id: str) -> Optional[OAuthToken]:
        """
        Get OAuth token from database.
        
        Args:
            user_id: User identifier
            
        Returns:
            OAuthToken instance or None
        """
        with get_db() as db:
            token = db.query(OAuthToken).filter(
                OAuthToken.user_id == user_id
            ).first()
            
            if token and token.is_expired():
                logger.info(f"Token expired for user {user_id}, refreshing...")
                # Refresh token
                new_token_data = self.refresh_access_token(token.refresh_token)
                self.save_token(user_id, new_token_data)
                # Get updated token
                token = db.query(OAuthToken).filter(
                    OAuthToken.user_id == user_id
                ).first()
            
            return token
    
    def get_access_token(self, user_id: str) -> Optional[str]:
        """
        Get valid access token for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Access token string or None
        """
        token = self.get_token(user_id)
        return token.access_token if token else None