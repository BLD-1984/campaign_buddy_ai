# test_nb_api.py
"""
Simple test script to verify NationBuilder API v2 access
Run this first to ensure your credentials work
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to Python path
sys.path.append('src')

from nb_api_client import NationBuilderClient, NationBuilderAPIError


def load_credentials():
    """Load credentials from environment variables"""
    # Map your .env variable names to what the client expects
    env_mapping = {
        'nation_slug': 'NB_NATION_SLUG',
        'access_token': 'NB_PA_TOKEN', 
        'refresh_token': 'NB_PA_TOKEN_REFRESH',
        'client_id': 'NB_PA_ID',
        'client_secret': 'NB_PA_SECRET'
    }
    
    credentials = {}
    
    # Load all credentials
    for key, env_var in env_mapping.items():
        value = os.getenv(env_var)
        if key in ['nation_slug', 'access_token'] and not value:
            raise ValueError(f"Missing required environment variable: {env_var}")
        if value:
            credentials[key] = value
    
    return credentials


def test_basic_api_access():
    """Test basic API functionality"""
    print("🔍 Testing NationBuilder API v2 Access")
    print("=" * 50)
    
    try:
        # Load credentials
        creds = load_credentials()
        print(f"✅ Loaded credentials for nation: {creds['nation_slug']}")
        
        # Initialize client
        client = NationBuilderClient(
            nation_slug=creds['nation_slug'],
            access_token=creds['access_token'],
            refresh_token=creds.get('refresh_token'),
            client_id=creds.get('client_id'),
            client_secret=creds.get('client_secret')
        )
        
        # Test connection
        print("\n🔗 Testing API connection...")
        if not client.test_connection():
            print("❌ Connection test failed")
            return False
            
        print("✅ API connection successful!")
        
        # Get basic signup count
        print("\n📊 Getting signup statistics...")
        result = client.get_signups(fields=['first_name', 'last_name'], page_size=1)
        
        # Try to get count (if supported)
        count_result = client.get_signups(page_size=1)
        print(f"✅ API responding normally")
        
        # Show sample data structure
        if result.get('data'):
            sample_signup = result['data'][0]
            print(f"\n📋 Sample signup structure:")
            print(f"   ID: {sample_signup.get('id')}")
            print(f"   Type: {sample_signup.get('type')}")
            print(f"   Attributes: {list(sample_signup.get('attributes', {}).keys())}")
            if 'relationships' in sample_signup:
                print(f"   Relationships: {list(sample_signup.get('relationships', {}).keys())}")
        
        # Test getting a few more signups with different fields
        print("\n🔍 Testing field selection...")
        detailed_result = client.get_signups(
            fields=['first_name', 'last_name', 'email', 'support_level', 'created_at'],
            page_size=5
        )
        
        print(f"✅ Retrieved {len(detailed_result.get('data', []))} signups with custom fields")
        
        # Show some sample data
        for i, signup in enumerate(detailed_result.get('data', [])[:3]):
            attrs = signup.get('attributes', {})
            print(f"   {i+1}. {attrs.get('first_name', 'N/A')} {attrs.get('last_name', 'N/A')} - {attrs.get('email', 'N/A')}")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_filtering():
    """Test basic filtering functionality"""
    print("\n🔍 Testing Filtering Capabilities")
    print("=" * 50)
    
    try:
        creds = load_credentials()
        client = NationBuilderClient(
            nation_slug=creds['nation_slug'],
            access_token=creds['access_token'],
            refresh_token=creds.get('refresh_token'),
            client_id=creds.get('client_id'),
            client_secret=creds.get('client_secret')
        )
        
        # Test simple filter - people with email addresses (using a simpler filter)
        print("🔍 Testing filter: signups with support level...")
        # Try a simple numeric filter instead
        support_filter = {'support_level': {'gte': 0}}
        
        result = client.get_signups(
            filters=support_filter,
            fields=['first_name', 'last_name', 'email', 'support_level'],
            page_size=10
        )
        
        signups_with_support = result.get('data', [])
        print(f"✅ Found {len(signups_with_support)} signups with support level filter")
        
        # Show samples
        for i, signup in enumerate(signups_with_support[:3]):
            attrs = signup.get('attributes', {})
            support = attrs.get('support_level', 'N/A')
            print(f"   {i+1}. {attrs.get('first_name', 'N/A')} {attrs.get('last_name', 'N/A')} - Support: {support}")
        
        # Test date-based filter - recent signups
        print("\n🔍 Testing filter: recent signups (last 30 days)...")
        from datetime import datetime, timedelta
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        date_filter = {'created_at': {'gte': thirty_days_ago}}
        
        recent_result = client.get_signups(
            filters=date_filter,
            fields=['first_name', 'last_name', 'created_at'],
            page_size=10
        )
        
        recent_signups = recent_result.get('data', [])
        print(f"✅ Found {len(recent_signups)} recent signups")
        
        print("\n🎉 Filtering tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Filtering test failed: {e}")
        return False


def test_paths():
    """Test path and path step functionality"""
    print("\n🔍 Testing Path Functionality")
    print("=" * 50)
    
    try:
        creds = load_credentials()
        client = NationBuilderClient(
            nation_slug=creds['nation_slug'],
            access_token=creds['access_token'],
            refresh_token=creds.get('refresh_token'),
            client_id=creds.get('client_id'),
            client_secret=creds.get('client_secret')
        )
        
        # Get available paths
        print("🔍 Getting available paths...")
        paths_result = client.get_paths()
        paths = paths_result.get('data', [])
        
        print(f"✅ Found {len(paths)} paths in your nation")
        
        # Show path details
        for i, path in enumerate(paths[:5]):  # Show first 5 paths
            attrs = path.get('attributes', {})
            print(f"   {i+1}. Path ID: {path.get('id')} - Name: {attrs.get('name', 'N/A')}")
            
            # Get steps for this path
            if i == 0 and path.get('id'):  # Just test the first path
                print(f"      Getting steps for path {path.get('id')}...")
                try:
                    steps_result = client.get_path_steps(path.get('id'))
                    steps = steps_result.get('data', [])
                    print(f"      Found {len(steps)} steps")
                    
                    for j, step in enumerate(steps[:3]):  # Show first 3 steps
                        step_attrs = step.get('attributes', {})
                        print(f"         Step {j+1}: {step.get('id')} - {step_attrs.get('name', 'N/A')}")
                        
                except Exception as step_error:
                    print(f"      ⚠️  Could not get steps: {step_error}")
        
        print("\n🎉 Path tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Path test failed: {e}")
        return False


def main():
    """Run all tests"""
    print(f"🚀 NationBuilder API v2 Test Suite")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check environment setup
    print("🔧 Environment Setup:")
    required_vars = ['NB_NATION_SLUG', 'NB_PA_TOKEN']
    optional_vars = ['NB_PA_TOKEN_REFRESH', 'NB_PA_ID', 'NB_PA_SECRET']
    
    for var in required_vars:
        status = "✅" if os.getenv(var) else "❌"
        print(f"   {status} {var} (required)")
        
    for var in optional_vars:
        status = "✅" if os.getenv(var) else "⚠️ "
        print(f"   {status} {var} (optional)")
    
    print("\n")
    
    # Run tests
    tests = [
        ("Basic API Access", test_basic_api_access),
        ("Filtering", test_filtering),
        ("Paths & Steps", test_paths),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 30)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! Your NationBuilder API setup is working correctly.")
        print("\nNext steps:")
        print("1. Create your complex filter criteria")
        print("2. Build the path assignment logic")
        print("3. Set up Cloud Function deployment")
    else:
        print("\n⚠️  Some tests failed. Please check your credentials and try again.")


if __name__ == "__main__":
    main()