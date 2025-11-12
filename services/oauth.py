"""OAuth2 authentication service for Oura API."""
import os
import secrets
import webbrowser
from datetime import datetime, timedelta, timezone
from typing import Optional

from requests_oauthlib import OAuth2Session

from config import settings
from models.auth import OAuthToken
from utils import logger
from utils.database import get_db

# Allow OAuth over HTTP for local development (localhost redirect URIs)
# This is safe because the redirect is to localhost only
if settings.oura_redirect_uri.startswith('http://localhost') or settings.oura_redirect_uri.startswith('http://127.0.0.1'):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Disable strict scope checking - Oura returns scopes with 'extapi:' prefix
# but we request them without prefix (e.g., 'daily' vs 'extapi:daily')
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


class OuraOAuth:
    """Handle OAuth2 authentication flow with Oura API."""

    # Oura API endpoints (per https://cloud.ouraring.com/docs/authentication)
    AUTHORIZATION_URL = "https://cloud.ouraring.com/oauth/authorize"
    TOKEN_URL = "https://api.ouraring.com/oauth/token"
    REVOKE_URL = "https://api.ouraring.com/oauth/revoke"

    def __init__(self):
        self.client_id = settings.oura_client_id
        self.client_secret = settings.oura_client_secret
        self.redirect_uri = settings.oura_redirect_uri
        self.scopes = settings.oauth_scopes

    def _create_oauth_session(self, state: Optional[str] = None, token: Optional[dict] = None) -> OAuth2Session:
        """
        Create an OAuth2Session with proper configuration.

        Args:
            state: Optional state parameter for CSRF protection
            token: Optional existing token dict

        Returns:
            Configured OAuth2Session
        """
        return OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scopes,
            state=state,
            token=token,
            auto_refresh_url=self.TOKEN_URL,
            auto_refresh_kwargs={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            },
            token_updater=self._token_updater
        )

    def _token_updater(self, token: dict):
        """
        Callback for automatic token refresh.
        Note: This is called by OAuth2Session when token auto-refreshes.

        Args:
            token: New token dict from refresh
        """
        logger.info("Token auto-refreshed by OAuth2Session")
        # The token will be saved by the caller who has user_id context

    def get_authorization_url(self) -> tuple[str, str]:
        """
        Generate the authorization URL for user consent with CSRF protection.

        Returns:
            Tuple of (authorization_url, state) where state must be verified in callback
        """
        oauth = self._create_oauth_session()
        authorization_url, state = oauth.authorization_url(self.AUTHORIZATION_URL)

        logger.info("Authorization URL generated with state parameter")
        return authorization_url, state

    def start_auth_flow(self) -> tuple[str, str]:
        """
        Start the OAuth flow by opening browser and getting authorization code.

        Returns:
            Tuple of (authorization_code, state)
        """
        auth_url, state = self.get_authorization_url()

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
        print("After authorizing, you'll be redirected to:")
        print(f"{self.redirect_uri}?code=XXXX&state=XXXX\n")
        auth_code = input("Enter the authorization code from the redirect URL: ").strip()

        return auth_code, state

    def exchange_code_for_token(self, auth_code: str, state: Optional[str] = None) -> dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            auth_code: Authorization code from OAuth callback
            state: State parameter for CSRF verification (optional but recommended)

        Returns:
            Token response dictionary
        """
        oauth = self._create_oauth_session(state=state)

        try:
            # Construct the full callback URL that the OAuth provider redirected to
            authorization_response = f"{self.redirect_uri}?code={auth_code}"
            if state:
                authorization_response += f"&state={state}"

            # Fetch the token - this validates state and exchanges code
            token = oauth.fetch_token(
                self.TOKEN_URL,
                authorization_response=authorization_response,
                client_secret=self.client_secret,
                include_client_id=True
            )

            logger.info("Successfully exchanged authorization code for tokens")
            return token

        except Exception as e:
            logger.error(f"Token exchange failed: {str(e)}")
            raise Exception(f"Failed to exchange code for token: {str(e)}")

    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token using refresh token.

        IMPORTANT: Oura refresh tokens are single-use! The new response
        will contain a NEW refresh token that must be saved.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response dictionary (includes new refresh token)
        """
        oauth = self._create_oauth_session()

        try:
            # Use the extra parameter for refresh_token
            extra = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }

            token = oauth.refresh_token(
                self.TOKEN_URL,
                refresh_token=refresh_token,
                **extra
            )

            logger.info("Successfully refreshed access token (new refresh token received)")
            return token

        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise Exception(f"Failed to refresh token: {str(e)}")
    
    def save_token(self, user_id: str, token_data: dict):
        """
        Save OAuth token to database.

        IMPORTANT: Always call this after refresh to save the new refresh token,
        as Oura refresh tokens are single-use!

        Args:
            user_id: User identifier
            token_data: Token response from Oura API
        """
        with get_db() as db:
            # Calculate token expiration (use UTC timezone-aware datetime)
            expires_in = token_data.get("expires_in", 86400)  # Default 24 hours
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            # Check if token exists
            existing_token = db.query(OAuthToken).filter(
                OAuthToken.user_id == user_id
            ).first()

            if existing_token:
                # Update existing token (including new refresh token!)
                existing_token.access_token = token_data["access_token"]
                existing_token.refresh_token = token_data.get("refresh_token", existing_token.refresh_token)
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
        Get OAuth token from database, automatically refreshing if expired.

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
                try:
                    # Refresh token - this returns a NEW refresh token!
                    new_token_data = self.refresh_access_token(token.refresh_token)
                    self.save_token(user_id, new_token_data)
                    # Get updated token
                    token = db.query(OAuthToken).filter(
                        OAuthToken.user_id == user_id
                    ).first()
                except Exception as e:
                    logger.error(f"Failed to refresh token for user {user_id}: {e}")
                    # Return None to indicate authentication is needed
                    return None

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

    def create_authenticated_session(self, user_id: str) -> Optional[OAuth2Session]:
        """
        Create an OAuth2Session with a valid token for making API requests.
        The session will automatically refresh tokens when they expire.

        Args:
            user_id: User identifier

        Returns:
            OAuth2Session configured with user's token, or None if not authenticated
        """
        # Get token and extract all needed attributes while DB session is active
        with get_db() as db:
            token_obj = db.query(OAuthToken).filter(
                OAuthToken.user_id == user_id
            ).first()

            if not token_obj:
                return None

            # Check if expired and refresh if needed
            if token_obj.is_expired():
                logger.info(f"Token expired for user {user_id}, refreshing...")
                try:
                    new_token_data = self.refresh_access_token(token_obj.refresh_token)
                    self.save_token(user_id, new_token_data)
                    # Re-query to get fresh token
                    token_obj = db.query(OAuthToken).filter(
                        OAuthToken.user_id == user_id
                    ).first()
                except Exception as e:
                    logger.error(f"Failed to refresh token for user {user_id}: {e}")
                    return None

            # Extract all attributes while session is still active
            # Ensure both datetimes are timezone-aware for comparison
            now = datetime.now(timezone.utc)
            expires_at = token_obj.expires_at

            # If expires_at is naive, make it timezone-aware (assume UTC)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            token_dict = {
                'access_token': token_obj.access_token,
                'refresh_token': token_obj.refresh_token,
                'token_type': token_obj.token_type,
                'expires_in': int((expires_at - now).total_seconds()),
            }

        # Create session that will auto-refresh and save via callback
        def token_saver(token):
            self.save_token(user_id, token)

        session = OAuth2Session(
            client_id=self.client_id,
            token=token_dict,
            auto_refresh_url=self.TOKEN_URL,
            auto_refresh_kwargs={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            },
            token_updater=token_saver
        )

        return session