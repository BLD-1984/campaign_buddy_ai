# tests/nb_path_nightly/test_filters_clickers.py

import sys
import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from datetime import datetime

# Add the project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(project_root, 'nb_path_updates', 'nb_nightly', 'filters'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from nb_path_updates.nb_path_nightly.filters import clickers
from src.nb_api_client import NationBuilderAPIError


class DummyLogger:
    def __init__(self):
        self.messages = []
    
    def info(self, msg):
        self.messages.append(f"INFO: {msg}")
        print(f"INFO: {msg}")
    
    def debug(self, msg):
        self.messages.append(f"DEBUG: {msg}")
        print(f"DEBUG: {msg}")
    
    def warning(self, msg):
        self.messages.append(f"WARNING: {msg}")
        print(f"WARNING: {msg}")
    
    def error(self, msg):
        self.messages.append(f"ERROR: {msg}")
        print(f"ERROR: {msg}")


class DummyResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
    
    def json(self):
        return self.data


class DummyClient:
    def __init__(self, journey_type="active"):
        """
        journey_type: "active", "inactive", "none", or "error"
        """
        self.journey_type = journey_type
        self.base_url = "https://test.nationbuilder.com/api/v2"
    
    def get_signup_taggings(self, filters=None, page_size=100):
        """Return mock signup taggings"""
        if filters and filters.get('tag_id') == "14890":
            return {
                'data': [
                    {
                        'id': '1',
                        'type': 'signup_taggings',
                        'attributes': {
                            'signup_id': '123',
                            'tag_id': '14890'
                        }
                    },
                    {
                        'id': '2', 
                        'type': 'signup_taggings',
                        'attributes': {
                            'signup_id': '456',
                            'tag_id': '14890'
                        }
                    }
                ]
            }
        return {'data': []}
    
    def list_exists(self, slug):
        """Mock list existence check - always return None (doesn't exist)"""
        return None
    
    def create_list(self, slug, name, author_id):
        """Mock list creation"""
        return {
            'data': {
                'id': '789',
                'type': 'lists',
                'attributes': {
                    'slug': slug,
                    'name': name
                }
            }
        }
    
    def add_people_to_list(self, list_id, signup_ids):
        """Mock adding people to list"""
        return {
            'data': {
                'id': list_id,
                'type': 'lists'
            }
        }
    
    def _make_request(self, method, url, params=None, json=None):
        """Mock HTTP requests for path journey operations"""
        # Handle path journey queries
        if '/path_journeys' in url and method == 'GET':
            if 'filter[signup_id]' in (params or {}):
                signup_id = params['filter[signup_id]']
                return self._get_mock_journey_response(signup_id)
        
        # Handle journey updates/creation
        elif '/path_journeys' in url and method in ['POST', 'PATCH']:
            return DummyResponse({'data': {'id': '999', 'type': 'path_journeys'}})
        
        # Handle reactivation
        elif '/reactivate' in url and method == 'PATCH':
            return DummyResponse({'data': {'id': '999', 'type': 'path_journeys'}})
        
        # Default response
        return DummyResponse({'data': []})
    
    def _handle_response(self, response):
        """Mock response handling"""
        if response.status_code >= 400:
            raise NationBuilderAPIError(f"API Error {response.status_code}")
        return response.json()
    
    def _get_mock_journey_response(self, signup_id):
        """Return mock journey data based on journey_type"""
        if self.journey_type == "none":
            # No journeys exist
            return DummyResponse({'data': []})
        
        elif self.journey_type == "active":
            # Active journey on different step
            return DummyResponse({
                'data': [{
                    'id': '888',
                    'type': 'path_journeys',
                    'attributes': {
                        'signup_id': signup_id,
                        'path_id': '1109',
                        'current_step_id': '999',  # Different step
                        'journey_status': 'active'
                    }
                }]
            })
        
        elif self.journey_type == "inactive":
            # Inactive journey
            return DummyResponse({
                'data': [{
                    'id': '888',
                    'type': 'path_journeys', 
                    'attributes': {
                        'signup_id': signup_id,
                        'path_id': '1109',
                        'current_step_id': '999',
                        'journey_status': 'inactive'
                    }
                }]
            })
        
        elif self.journey_type == "error":
            # Simulate API error
            return DummyResponse({'error': 'API Error'}, status_code=500)
        
        else:
            return DummyResponse({'data': []})
    
    def update_path_journey_step(self, journey_id, step_id):
        """Mock journey step update"""
        if self.journey_type == "error":
            raise NationBuilderAPIError("Mock API Error")
        return {'data': {'id': journey_id, 'type': 'path_journeys'}}
    
    def reactivate_path_journey(self, journey_id, step_id):
        """Mock journey reactivation"""
        if self.journey_type == "error":
            raise NationBuilderAPIError("Mock API Error")
        return {'data': {'id': journey_id, 'type': 'path_journeys'}}
    
    def create_path_journey(self, signup_id, path_id, step_id):
        """Mock journey creation"""
        if self.journey_type == "error":
            raise NationBuilderAPIError("Mock API Error")
        return {'data': {'id': '999', 'type': 'path_journeys'}}


def test_find_signup_ids_with_tag_id():
    """Test finding signup IDs with specific tag"""
    client = DummyClient()
    logger = DummyLogger()
    
    signup_ids = clickers.find_signup_ids_with_tag_id(client, "14890", logger)
    
    assert len(signup_ids) == 2
    assert "123" in signup_ids
    assert "456" in signup_ids


def test_export_signup_ids_to_csv():
    """Test CSV export functionality"""
    logger = DummyLogger()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Temporarily change the output directory
        original_dirname = clickers.__file__
        clickers.__file__ = os.path.join(temp_dir, "clickers.py")
        
        try:
            filepath = clickers.export_signup_ids_to_csv(["123", "456"], "14890", logger)
            
            assert filepath is not None
            assert os.path.exists(filepath)
            
            # Read and verify CSV content
            with open(filepath, 'r') as f:
                content = f.read()
                assert "123" in content
                assert "456" in content
                assert "14890" in content
                
        finally:
            clickers.__file__ = original_dirname


def test_process_signup_path_journey_create():
    """Test creating new path journey"""
    client = DummyClient(journey_type="none")
    logger = DummyLogger()
    
    result = clickers.process_signup_path_journey(client, "123", logger)
    assert result is True


def test_process_signup_path_journey_update():
    """Test updating existing active journey"""
    client = DummyClient(journey_type="active")
    logger = DummyLogger()
    
    result = clickers.process_signup_path_journey(client, "123", logger)
    assert result is True


def test_process_signup_path_journey_reactivate():
    """Test reactivating inactive journey"""
    client = DummyClient(journey_type="inactive") 
    logger = DummyLogger()
    
    result = clickers.process_signup_path_journey(client, "123", logger)
    assert result is True


def test_process_signup_path_journey_error():
    """Test handling API errors"""
    client = DummyClient(journey_type="error")
    logger = DummyLogger()
    
    result = clickers.process_signup_path_journey(client, "123", logger)
    assert result is False


def test_run_filter(monkeypatch):
    """Test the main run_filter function"""
    monkeypatch.setenv("NB_ADMIN_SIGNUP_ID", "admin123")
    
    client = DummyClient()
    logger = DummyLogger()
    
    result = clickers.run_filter(client, logger)
    
    # Assert all expected keys are present
    expected_keys = [
        'people_count', 'csv_filename', 'list_slug', 'list_id',
        'path_updates_successful', 'path_updates_errors'
    ]
    for key in expected_keys:
        assert key in result
    
    assert result['people_count'] == 2
    assert result['csv_filename'] is not None
    assert result['list_slug'] is not None
    assert result['list_id'] == '789'
    assert result['path_updates_successful'] == 2
    assert result['path_updates_errors'] == 0


def test_run_filter_create_journey(monkeypatch):
    """Test run_filter with journey creation scenario"""
    monkeypatch.setenv("NB_ADMIN_SIGNUP_ID", "admin123")
    
    client = DummyClient(journey_type="none")
    logger = DummyLogger()
    
    result = clickers.run_filter(client, logger)
    
    expected_keys = [
        'people_count', 'csv_filename', 'list_slug', 'list_id',
        'path_updates_successful', 'path_updates_errors'
    ]
    for key in expected_keys:
        assert key in result
        
    assert result['people_count'] == 2
    assert result['path_updates_successful'] == 2
    assert result['path_updates_errors'] == 0


def test_run_filter_update_journey(monkeypatch):
    """Test run_filter with journey update scenario"""
    monkeypatch.setenv("NB_ADMIN_SIGNUP_ID", "admin123")
    
    client = DummyClient(journey_type="active")
    logger = DummyLogger()
    
    result = clickers.run_filter(client, logger)
    
    expected_keys = [
        'people_count', 'csv_filename', 'list_slug', 'list_id', 
        'path_updates_successful', 'path_updates_errors'
    ]
    for key in expected_keys:
        assert key in result
        
    assert result['people_count'] == 2
    assert result['path_updates_successful'] == 2
    assert result['path_updates_errors'] == 0


def test_run_filter_reactivate_journey(monkeypatch):
    """Test run_filter with journey reactivation scenario"""
    monkeypatch.setenv("NB_ADMIN_SIGNUP_ID", "admin123")
    
    client = DummyClient(journey_type="inactive")
    logger = DummyLogger()
    
    result = clickers.run_filter(client, logger)
    
    expected_keys = [
        'people_count', 'csv_filename', 'list_slug', 'list_id',
        'path_updates_successful', 'path_updates_errors'
    ]
    for key in expected_keys:
        assert key in result
        
    assert result['people_count'] == 2
    assert result['path_updates_successful'] == 2
    assert result['path_updates_errors'] == 0


def test_run_filter_with_errors(monkeypatch):
    """Test run_filter handling API errors"""
    monkeypatch.setenv("NB_ADMIN_SIGNUP_ID", "admin123")
    
    client = DummyClient(journey_type="error")
    logger = DummyLogger()
    
    result = clickers.run_filter(client, logger)
    
    expected_keys = [
        'people_count', 'csv_filename', 'list_slug', 'list_id',
        'path_updates_successful', 'path_updates_errors'
    ]
    for key in expected_keys:
        assert key in result
        
    assert result['people_count'] == 2
    assert result['path_updates_successful'] == 0
    assert result['path_updates_errors'] == 2


def test_run_filter_no_admin_id():
    """Test run_filter without admin signup ID"""
    client = DummyClient()
    logger = DummyLogger()
    
    # Make sure NB_ADMIN_SIGNUP_ID is not set
    if 'NB_ADMIN_SIGNUP_ID' in os.environ:
        del os.environ['NB_ADMIN_SIGNUP_ID']
    
    result = clickers.run_filter(client, logger)
    
    assert result['people_count'] == 2
    assert result['list_id'] is None  # Should be None due to missing admin ID


def test_run_filter_no_signups():
    """Test run_filter when no signups found"""
    class EmptyClient(DummyClient):
        def get_signup_taggings(self, filters=None, page_size=100):
            return {'data': []}
    
    client = EmptyClient()
    logger = DummyLogger()
    
    result = clickers.run_filter(client, logger)
    
    assert result['people_count'] == 0
    assert result['csv_filename'] is None
    assert result['list_slug'] is None
    assert result['list_id'] is None