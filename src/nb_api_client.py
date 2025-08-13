# src/nb_api_client.py
"""
NationBuilder API v2 Client
Enhanced with proper OAuth 2.0 refresh token flow for production use
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NationBuilderAPIError(Exception):
    """Custom exception for NationBuilder API errors"""
    pass


class NationBuilderClient:
    """
    NationBuilder API v2 Client
    
    Handles authentication, rate limiting, and automatic token refresh
    Production-ready for Google Cloud Functions and local development
    """
    
    def __init__(self, nation_slug: str, access_token: str, refresh_token: str = None, 
                 client_id: str = None, client_secret: str = None):
        self.nation_slug = nation_slug
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = f"https://{nation_slug}.nationbuilder.com/api/v2"
        self.oauth_url = f"https://{nation_slug}.nationbuilder.com/oauth/token"
        
        # Track token refresh attempts to prevent infinite loops
        self._refresh_attempts = 0
        self._max_refresh_attempts = 2
        
        # Initialize session
        self.session = requests.Session()
        self._update_session_headers()
        
    def _update_session_headers(self):
        """Update session headers with current access token"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        })
        
    def refresh_access_token(self):
        """
        Refresh the access token using refresh token
        This is the core of the V2 OAuth flow for production use
        """
        if not all([self.refresh_token, self.client_id, self.client_secret]):
            raise NationBuilderAPIError(
                "Missing credentials for token refresh. Need refresh_token, client_id, and client_secret."
            )
        
        logger.info(" Refreshing access token...")
        
        # Prepare refresh request data
        refresh_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        # Make refresh request (don't use self.session to avoid auth headers)
        refresh_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            response = requests.post(self.oauth_url, data=refresh_data, headers=refresh_headers)
            
            if response.status_code == 200:
                token_data = response.json()
                
                # Update tokens
                old_access_token = self.access_token[:20] + "..." if self.access_token else "None"
                self.access_token = token_data['access_token']
                self.refresh_token = token_data['refresh_token']  # Important: refresh token also changes!
                
                # Update session headers with new token
                self._update_session_headers()
                
                logger.info(f" Token refresh successful")
                logger.debug(f"   Old token: {old_access_token}")
                logger.debug(f"   New token: {self.access_token[:20]}...")
                
                # Update environment variables if running locally (for persistence)
                self._update_env_file_if_local()
                
                return True
                
            else:
                error_msg = f"Token refresh failed with status {response.status_code}: {response.text}"
                logger.error(f" {error_msg}")
                raise NationBuilderAPIError(error_msg)
                
        except requests.RequestException as e:
            error_msg = f"Network error during token refresh: {e}"
            logger.error(f" {error_msg}")
            raise NationBuilderAPIError(error_msg)
    
    def _update_env_file_if_local(self):
        """
        Update .env file with new tokens if running locally
        This helps persist tokens between local test runs
        """
        try:
            # Only do this if we can detect we're in a local environment
            if os.path.exists('.env') and not os.getenv('GOOGLE_CLOUD_PROJECT'):
                logger.debug(" Updating local .env file with new tokens")
                
                # Read current .env file
                env_lines = []
                with open('.env', 'r') as f:
                    env_lines = f.readlines()
                
                # Update token lines
                updated_lines = []
                access_token_updated = False
                refresh_token_updated = False
                
                for line in env_lines:
                    if line.startswith('NB_PA_TOKEN=') and not line.startswith('NB_PA_TOKEN_REFRESH='):
                        updated_lines.append(f'NB_PA_TOKEN={self.access_token}\n')
                        access_token_updated = True
                    elif line.startswith('NB_PA_TOKEN_REFRESH='):
                        updated_lines.append(f'NB_PA_TOKEN_REFRESH={self.refresh_token}\n')
                        refresh_token_updated = True
                    else:
                        updated_lines.append(line)
                
                # Add tokens if they weren't found
                if not access_token_updated:
                    updated_lines.append(f'NB_PA_TOKEN={self.access_token}\n')
                if not refresh_token_updated:
                    updated_lines.append(f'NB_PA_TOKEN_REFRESH={self.refresh_token}\n')
                
                # Write updated .env file
                with open('.env', 'w') as f:
                    f.writelines(updated_lines)
                    
        except Exception as e:
            logger.debug(f"Could not update .env file: {e}")
            # This is non-critical, so we don't raise an exception
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with automatic token refresh on 401 errors
        This is the key method that handles token expiration transparently
        """
        # Reset refresh attempts counter for new requests
        if self._refresh_attempts >= self._max_refresh_attempts:
            self._refresh_attempts = 0
        
        # Make the initial request
        response = self.session.request(method, url, **kwargs)
        
        # Handle 401 (Unauthorized) - likely expired token
        if response.status_code == 401 and self._refresh_attempts < self._max_refresh_attempts:
            logger.info(" Got 401 Unauthorized, attempting token refresh...")
            self._refresh_attempts += 1
            
            try:
                # Try to refresh the token
                self.refresh_access_token()
                
                # Retry the original request with the new token
                logger.debug(" Retrying original request with refreshed token...")
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code != 401:
                    logger.info(" Request successful after token refresh")
                    self._refresh_attempts = 0  # Reset counter on success
                    
            except NationBuilderAPIError as e:
                logger.error(f" Token refresh failed: {e}")
                # Don't retry further, let the 401 response be handled downstream
        
        return response
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors"""
        try:
            if response.status_code >= 400:
                error_details = ""
                try:
                    error_data = response.json()
                    error_details = f" - {error_data}"
                except:
                    error_details = f" - {response.text}"
                
                error_msg = f"API Error {response.status_code}{error_details}"
                logger.error(error_msg)
                raise NationBuilderAPIError(error_msg)
                
            return response.json()
            
        except json.JSONDecodeError:
            raise NationBuilderAPIError(f"Invalid JSON response: {response.text}")
    
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
        
        response = self._make_request('GET', url, params=params)
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
            
        response = self._make_request('GET', url, params=params)
        return self._handle_response(response)
    
    def get_signup_tags(self, filters: Dict[str, Any] = None, 
                       page_size: int = 100) -> Dict[str, Any]:
        """Get signup tags with optional filtering"""
        url = f"{self.base_url}/signup_tags"
        params = {'page[size]': min(page_size, 100)}
        
        if filters:
            for key, value in filters.items():
                params[f'filter[{key}]'] = value
                
        response = self._make_request('GET', url, params=params)
        return self._handle_response(response)
    
    def get_signup_taggings(self, filters: Dict[str, Any] = None,
                           include: List[str] = None,
                           page_size: int = 100) -> Dict[str, Any]:
        """Get signup taggings (relationships between signups and tags)"""
        url = f"{self.base_url}/signup_taggings"
        params = {'page[size]': min(page_size, 100)}
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    params[f'filter[{key}]'] = ','.join(map(str, value))
                else:
                    params[f'filter[{key}]'] = value
        
        if include:
            params['include'] = ','.join(include)
            
        response = self._make_request('GET', url, params=params)
        return self._handle_response(response)
    
    def get_path_journeys(self, filters: Dict[str, Any] = None,
                         page_size: int = 100) -> Dict[str, Any]:
        """Get path journeys with optional filtering"""
        url = f"{self.base_url}/path_journeys"
        params = {'page[size]': min(page_size, 100)}
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    params[f'filter[{key}]'] = ','.join(map(str, value))
                else:
                    params[f'filter[{key}]'] = value
                    
        response = self._make_request('GET', url, params=params)
        return self._handle_response(response)
    
    def get_paths(self) -> Dict[str, Any]:
        """Get all paths in the nation"""
        url = f"{self.base_url}/paths"
        response = self._make_request('GET', url)
        return self._handle_response(response)
    
    def get_path_steps(self, path_id: str) -> Dict[str, Any]:
        """Get steps for a specific path"""
        url = f"{self.base_url}/path_steps"
        params = {'filter[path_id]': path_id}
        response = self._make_request('GET', url, params=params)
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
        
        response = self._make_request('POST', url, json=data)
        return self._handle_response(response)
    
    def test_connection(self) -> bool:
        """Test the API connection by fetching nation info"""
        try:
            # Simple test - get first page of signups with minimal data
            result = self.get_signups(fields=['first_name', 'last_name'], page_size=1)
            logger.info(" API connection test successful")
            return True
        except Exception as e:
            logger.error(f" API connection test failed: {e}")
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
        
        # logger.info(f"Total signups fetched: {total_fetched}")
        # return 
        logger.info(f"Total signups fetched: {total_fetched}")
        return all_signups  # <-- Make sure this returns all_signups, not None



    def list_exists(self, slug: str) -> Optional[Dict[str, Any]]:
        """Check if a list with the given slug exists. Returns list dict if found, else None."""
        url = f"{self.base_url}/lists"
        params = {'filter[slug]': slug}
        response = self._make_request('GET', url, params=params)
        data = self._handle_response(response)
        lists = data.get('data', [])
        return lists[0] if lists else None

    def create_list(self, slug: str, name: str, author_id: str) -> Dict[str, Any]:
        """Create a new list with the given slug, name, and author."""
        url = f"{self.base_url}/lists"
        data = {
            "data": {
                "type": "lists",
                "attributes": {
                    "slug": slug,
                    "name": name
                },
                "relationships": {
                    "author": {
                        "data": {
                            "type": "signups",
                            "id": author_id
                        }
                    }
                }
            }
        }
        response = self._make_request('POST', url, json=data)
        return self._handle_response(response)

    # def add_people_to_list(self, list_id: str, signup_ids: List[str]) -> Dict[str, Any]:
    #     """Add multiple people to a list by list ID and signup IDs."""
    #     url = f"{self.base_url}/list_memberships/bulk"
    #     data = {
    #         "data": [
    #             {
    #                 "type": "list_memberships",
    #                 "attributes": {
    #                     "list_id": list_id,
    #                     "signup_id": signup_id
    #                 }
    #             }
    #             for signup_id in signup_ids
    #         ]
    #     }
    #     response = self._make_request('POST', url, json=data)
    #     return self._handle_response(response)
    
    # def add_people_to_list(self, list_id: str, signup_ids: List[str]) -> Dict[str, Any]:
    #     """Add multiple people to a list by list ID and signup IDs."""
    #     url = f"{self.base_url}/lists/{list_id}/relationships/signups"
    #     data = {
    #         "data": [
    #             {
    #                 "type": "signups",
    #                 "id": signup_id
    #             }
    #             for signup_id in signup_ids
    #         ]
    #     }
    #     logger.info(f"   ➡️ POST {url}")
    #     logger.info(f"   ➡️ Payload: {json.dumps(data)}")
    #     response = self._make_request('POST', url, json=data)
    #     logger.info(f"   ⬅️ Response status: {response.status_code}")
    #     logger.info(f"   ⬅️ Response text: {response.text}")
    #     return self._handle_response(response)
    
    def add_people_to_list(self, list_id: str, signup_ids: List[str]) -> Dict[str, Any]:
        """Add multiple people to a list by list ID and signup IDs using the async endpoint."""
        url = f"{self.base_url}/lists/{list_id}/add_signups"
        data = {
            "data": {
                "id": list_id,
                "type": "lists",
                "signup_ids": signup_ids
            }
        }
        logger.info(f"    PATCH {url}")
        logger.info(f"    Payload: {json.dumps(data)}")
        response = self._make_request('PATCH', url, json=data)
        logger.info(f"    Response status: {response.status_code}")
        logger.info(f"    Response text: {response.text}")
        return self._handle_response(response)

    def get_path_journey_for_signup(self, signup_id: str, path_id: str) -> Optional[Dict[str, Any]]:
        """Return the path journey for a signup and path, or None if not found."""
        url = f"{self.base_url}/path_journeys"
        params = {
            'filter[signup_id]': signup_id,
            'filter[path_id]': path_id,
            'page[size]': 1
        }
        response = self._make_request('GET', url, params=params)
        data = self._handle_response(response)
        journeys = data.get('data', [])
        return journeys[0] if journeys else None

    def update_path_journey_step(self, journey_id: str, step_id: str) -> Dict[str, Any]:
        """Update the current step of an existing path journey."""
        url = f"{self.base_url}/path_journeys/{journey_id}"
        data = {
            "data": {
                "id": journey_id,
                "type": "path_journeys",
                "attributes": {
                    "current_step_id": step_id
                }
            }
        }
        logger.debug(f"update_path_journey_step called with journey_id={journey_id}, step_id={step_id} (type={type(step_id)})")
        logger.info(f"    PATCH {url}")
        logger.info(f"    Payload: {json.dumps(data)}")
        response = self._make_request('PATCH', url, json=data)
        logger.info(f"    Response status: {response.status_code}")
        logger.info(f"    Response text: {response.text}")
        return self._handle_response(response)
    
    def reactivate_path_journey(self, journey_id: str, step_id: str) -> Dict[str, Any]:
        """Reactivate an inactive path journey at a specific step."""
        url = f"{self.base_url}/path_journeys/{journey_id}/reactivate"
        data = {
            "data": {
                "id": journey_id,
                "type": "path_journeys",
                "attributes": {
                    "current_step_id": step_id
                }
            }
        }
        logger.info(f"    PATCH {url}")
        logger.info(f"    Payload: {json.dumps(data)}")
        response = self._make_request('PATCH', url, json=data)
        logger.info(f"    Response status: {response.status_code}")
        logger.info(f"    Response text: {response.text}")
        return self._handle_response(response)

    def create_path_journey(self, signup_id: str, path_id: str, step_id: str) -> Dict[str, Any]:
        """Create a new path journey for a signup at a specific step."""
        url = f"{self.base_url}/path_journeys"
        data = {
            "data": {
                "type": "path_journeys",
                "attributes": {
                    "signup_id": signup_id,
                    "path_id": path_id,
                    "current_step_id": step_id
                }
            }
        }
        logger.info(f"    POST {url}")
        logger.info(f"    Payload: {json.dumps(data)}")
        response = self._make_request('POST', url, json=data)
        logger.info(f"    Response status: {response.status_code}")
        logger.info(f"    Response text: {response.text}")
        return self._handle_response(response)
