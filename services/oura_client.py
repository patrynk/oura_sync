"""Oura API client for fetching user data."""
import time
from datetime import date, datetime
from typing import Any, Optional

import requests

from config import settings
from services.oauth import OuraOAuth
from utils import logger


class OuraClient:
    """Client for interacting with Oura API."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.base_url = settings.oura_api_base_url
        self.oauth = OuraOAuth()
        self._session = requests.Session()
        
    def _get_headers(self) -> dict:
        """Get authorization headers."""
        access_token = self.oauth.get_access_token(self.user_id)
        if not access_token:
            raise Exception(f"No valid access token for user {self.user_id}")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[dict] = None,
        max_retries: int = 3
    ) -> dict:
        """
        Make API request with retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            max_retries: Maximum number of retries
            
        Returns:
            Response JSON data
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        for attempt in range(max_retries):
            try:
                response = self._session.get(url, headers=headers, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    # Try to refresh token
                    logger.info("Token invalid, attempting refresh...")
                    token = self.oauth.get_token(self.user_id)
                    if token:
                        new_token_data = self.oauth.refresh_access_token(token.refresh_token)
                        self.oauth.save_token(self.user_id, new_token_data)
                        continue
                    raise
                
                if attempt == max_retries - 1:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Request failed, retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
        
        raise Exception(f"Failed to complete request after {max_retries} attempts")
    
    def _fetch_paginated_data(
        self,
        endpoint: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> list[dict]:
        """
        Fetch all pages of paginated data.
        
        Args:
            endpoint: API endpoint
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            **kwargs: Additional query parameters
            
        Returns:
            List of all data items
        """
        all_data = []
        params = {**kwargs}
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        while True:
            response = self._make_request(endpoint, params)
            data = response.get("data", [])
            all_data.extend(data)
            
            # Check for next page
            next_token = response.get("next_token")
            if not next_token:
                break
            
            params["next_token"] = next_token
            logger.debug(f"Fetching next page (token: {next_token[:20]}...)")
        
        logger.info(f"Fetched {len(all_data)} items from {endpoint}")
        return all_data
    
    # Personal Info
    def get_personal_info(self) -> dict:
        """Get user personal information."""
        return self._make_request("/v2/usercollection/personal_info")
    
    # Daily Summaries
    def get_daily_activity(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily activity data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/daily_activity",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_daily_sleep(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily sleep data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/daily_sleep",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_daily_readiness(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily readiness data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/daily_readiness",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_daily_spo2(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily SpO2 data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/daily_spo2",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_daily_stress(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily stress data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/daily_stress",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_daily_resilience(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily resilience data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/daily_resilience",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_daily_cardiovascular_age(self, start_date: str, end_date: str) -> list[dict]:
        """Get daily cardiovascular age data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/daily_cardiovascular_age",
            start_date=start_date,
            end_date=end_date
        )
    
    # Time Series Data
    def get_heart_rate(self, start_datetime: str, end_datetime: str) -> list[dict]:
        """Get heart rate time series data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/heartrate",
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
    
    # Sleep Sessions
    def get_sleep(self, start_date: str, end_date: str) -> list[dict]:
        """Get sleep sessions data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/sleep",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_sleep_time(self, start_date: str, end_date: str) -> list[dict]:
        """Get sleep time recommendations."""
        return self._fetch_paginated_data(
            "/v2/usercollection/sleep_time",
            start_date=start_date,
            end_date=end_date
        )
    
    # Workouts & Sessions
    def get_workouts(self, start_date: str, end_date: str) -> list[dict]:
        """Get workout data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/workout",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_sessions(self, start_date: str, end_date: str) -> list[dict]:
        """Get session data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/session",
            start_date=start_date,
            end_date=end_date
        )
    
    # Tags
    def get_tags(self, start_date: str, end_date: str) -> list[dict]:
        """Get user tags."""
        return self._fetch_paginated_data(
            "/v2/usercollection/tag",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_enhanced_tags(self, start_date: str, end_date: str) -> list[dict]:
        """Get enhanced tags."""
        return self._fetch_paginated_data(
            "/v2/usercollection/enhanced_tag",
            start_date=start_date,
            end_date=end_date
        )
    
    # Other Data Types
    def get_rest_mode_periods(self, start_date: str, end_date: str) -> list[dict]:
        """Get rest mode period data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/rest_mode_period",
            start_date=start_date,
            end_date=end_date
        )
    
    def get_ring_configuration(self) -> list[dict]:
        """Get ring configuration data."""
        return self._fetch_paginated_data("/v2/usercollection/ring_configuration")
    
    def get_vo2_max(self, start_date: str, end_date: str) -> list[dict]:
        """Get VO2 max data."""
        return self._fetch_paginated_data(
            "/v2/usercollection/vO2_max",
            start_date=start_date,
            end_date=end_date
        )