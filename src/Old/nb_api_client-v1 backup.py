# src/nb_api_client.py
"""
NationBuilder API v2 Client
Modular client for interacting with NationBuilder's v2 API
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NationBuilderAPIError(Exception):
    """Custom exception for NationBuilder API errors"""
    pass


class NationBuilderClient:
    """
    NationBuilder API v2 Client
    
    Handles authentication, rate limiting, and API requests
    """
    
    def __init__(self, nation_slug: str, access_token: str, refresh_token: str = None, 
                 client_id: str = None, client_secret: str = None):
        self.nation_slug = nation_slug
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = f"https://{nation_slug}.nationbuilder.com/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        })
        
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors"""
        try:
            if response.status_code == 401:
                # Token might be expired, try to refresh
                if self.refresh_token and self.client_id and self.client_secret:
                    logger.info("Access token expired, attempting refresh...")
                    self.refresh_access_token()
                    # Retry the original request
                    response.request.headers['Authorization'] = f'Bearer {self.access_token}'
                    response = self.session.send(response.request)
                else:
                    raise NationBuilderAPIError("Access token expired and no refresh token available")
            
            if response.status_code >= 400:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise NationBuilderAPIError(error_msg)
                
            return response.json()
            
        except json.JSONDecodeError:
            raise NationBuilderAPIError(f"Invalid JSON response: {response.text}")
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not all([self.refresh_token, self.client_id, self.client_secret]):
            raise NationBuilderAPIError("Missing credentials for token refresh")
            
        refresh_url = f"https://{self.nation_slug}.nationbuilder.com/oauth/token"
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(refresh_url, data=data)
        if response.status_code != 200:
            raise NationBuilderAPIError(f"Token refresh failed: {response.text}")
            
        token_data = response.json()
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']  # Update refresh token too
        
        # Update session headers
        self.session.headers['Authorization'] = f'Bearer {self.access_token}'
        logger.info("Access token refreshed successfully")
    
    def get_signups(self, filters: Dict[str, Any] = None, fields: List[str] = None, 
                   include: List[str] = None, page_size: int = 20, 
                   page_number: int = 1) -> Dict[str, Any]:
        """
        Get signups with optional filtering, field selection, and sideloading
        
        Args:
            filters: Dictionary of filters (e.g., {'first_name': 'John'})
            fields: List of specific fields to return
            include: List of relationships to sideload
            page_size: Number of results per page (max 100)
            page_number: Page number to retrieve
        """
        url = f"{self.base_url}/signups"
        params = {
            'page[size]': min(page_size, 100),
            'page[number]': page_number
        }
        
        # Add filters
        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):
                    # Complex filter (e.g., {'support_level': {'gt': 1}})
                    for operator, filter_value in value.items():
                        params[f'filter[{key}][{operator}]'] = filter_value
                else:
                    # Simple filter
                    params[f'filter[{key}]'] = value
        
        # Add field selection
        if fields:
            params['fields[signups]'] = ','.join(fields)
            
        # Add includes
        if include:
            params['include'] = ','.join(include)
        
        response = self.session.get(url, params=params)
        return self._handle_response(response)
    
    def get_signup_by_id(self, signup_id: str, fields: List[str] = None, 
                        include: List[str] = None) -> Dict[str, Any]:
        """Get a specific signup by ID"""
        url = f"{self.base_url}/signups/{signup_id}"
        params = {}
        
        if fields:
            params['fields[signups]'] = ','.join(fields)
        if include:
            params['include'] = ','.join(include)
            
        response = self.session.get(url, params=params)
        return self._handle_response(response)
    
    def get_paths(self) -> Dict[str, Any]:
        """Get all paths in the nation"""
        url = f"{self.base_url}/paths"
        response = self.session.get(url)
        return self._handle_response(response)
    
    def get_path_steps(self, path_id: str) -> Dict[str, Any]:
        """Get steps for a specific path"""
        url = f"{self.base_url}/path_steps"
        params = {'filter[path_id]': path_id}
        response = self.session.get(url, params=params)
        return self._handle_response(response)
    
    def add_signup_to_path_step(self, signup_id: str, path_step_id: str) -> Dict[str, Any]:
        """Add a signup to a path step"""
        url = f"{self.base_url}/path_journeys"
        data = {
            "data": {
                "type": "path_journeys",
                "attributes": {
                    "signup_id": signup_id,
                    "path_step_id": path_step_id,
                    "status": "completed"  # or "in_progress" depending on your needs
                }
            }
        }
        
        response = self.session.post(url, json=data)
        return self._handle_response(response)
    
    def test_connection(self) -> bool:
        """Test the API connection by fetching nation info"""
        try:
            # Simple test - get first page of signups with minimal data
            result = self.get_signups(fields=['first_name', 'last_name'], page_size=1)
            logger.info("API connection test successful")
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
    
    def get_all_signups_paginated(self, filters: Dict[str, Any] = None, 
                                 fields: List[str] = None, 
                                 include: List[str] = None,
                                 max_results: int = None) -> List[Dict[str, Any]]:
        """
        Get all signups across multiple pages
        
        Args:
            max_results: Maximum number of results to return (None for all)
        """
        all_signups = []
        page = 1
        total_fetched = 0
        
        while True:
            page_size = 100  # Maximum page size
            if max_results and (total_fetched + page_size) > max_results:
                page_size = max_results - total_fetched
                
            result = self.get_signups(
                filters=filters, 
                fields=fields, 
                include=include,
                page_size=page_size,
                page_number=page
            )
            
            signups = result.get('data', [])
            if not signups:
                break
                
            all_signups.extend(signups)
            total_fetched += len(signups)
            
            logger.info(f"Fetched page {page}, {len(signups)} signups, total: {total_fetched}")
            
            if max_results and total_fetched >= max_results:
                break
                
            # Check if there are more pages
            if len(signups) < page_size:
                break
                
            page += 1
            
            # Be nice to the API
            time.sleep(0.1)
        
        logger.info(f"Total signups fetched: {total_fetched}")
        return all_signups
    