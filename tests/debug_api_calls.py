# tests/debug_api_calls.py
"""
Debug what we're actually calling in the NationBuilder API
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

from nb_api_client import NationBuilderClient


def load_client():
    return NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )


def debug_raw_api_call(client):
    """Debug the actual API call being made"""
    print("🐛 DEBUG: Raw API Call Analysis")
    print("-" * 50)
    
    # Let's see what URL we're actually calling
    base_url = client.base_url
    print(f"Base URL: {base_url}")
    
    # Test the exact endpoint
    url = f"{base_url}/signup_tags"
    print(f"Full URL: {url}")
    
    # Test with explicit parameters
    params = {'page[size]': 100, 'page[number]': 1}
    print(f"Parameters: {params}")
    
    # Make the raw request and see what we get
    try:
        response = client.session.get(url, params=params)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Analyze the response structure
            print(f"\n📊 Response Structure:")
            print(f"Top-level keys: {list(data.keys())}")
            
            if 'data' in data:
                tags = data['data']
                print(f"Number of tags in data: {len(tags)}")
                
                if len(tags) > 0:
                    first_tag = tags[0]
                    print(f"First tag structure: {list(first_tag.keys())}")
                    print(f"First tag ID: {first_tag.get('id')}")
                    print(f"First tag type: {first_tag.get('type')}")
                    
                    if 'attributes' in first_tag:
                        attrs = first_tag['attributes']
                        print(f"First tag name: '{attrs.get('name', 'N/A')}'")
                        print(f"First tag taggings_count: {attrs.get('taggings_count', 'N/A')}")
            
            if 'links' in data:
                links = data['links']
                print(f"\n🔗 Pagination Links:")
                for key, value in links.items():
                    print(f"  {key}: {value}")
                    
            if 'meta' in data:
                meta = data['meta']
                print(f"\n📋 Meta information:")
                print(f"  {meta}")
        
        else:
            print(f"❌ API call failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")


def test_pagination_manually(client):
    """Test pagination manually to understand the issue"""
    print(f"\n🔍 Manual Pagination Test")
    print("-" * 50)
    
    url = f"{client.base_url}/signup_tags"
    
    # Test first few pages manually
    for page_num in [1, 2, 3]:
        print(f"\n📄 Testing page {page_num}:")
        
        params = {'page[size]': 100, 'page[number]': page_num}
        
        try:
            response = client.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                tags = data.get('data', [])
                
                print(f"  Returned {len(tags)} tags")
                
                if len(tags) > 0:
                    # Show first and last tag ID in this page
                    first_id = tags[0].get('id')
                    last_id = tags[-1].get('id')
                    print(f"  Tag ID range: {first_id} to {last_id}")
                    
                    # Show first tag name
                    first_name = tags[0].get('attributes', {}).get('name', 'N/A')
                    print(f"  First tag: '{first_name}'")
                
                # Check if we're getting the same data
                if page_num > 1:
                    print(f"  Are we getting different data? Let's check...")
                
            else:
                print(f"  ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")


def test_with_correct_parameters(client):
    """Test with various parameter combinations"""
    print(f"\n🧪 Testing Different Parameter Combinations")
    print("-" * 50)
    
    url = f"{client.base_url}/signup_tags"
    
    # Test different approaches
    test_cases = [
        {"name": "No params", "params": {}},
        {"name": "Page size only", "params": {"page[size]": 10}},
        {"name": "Page number only", "params": {"page[number]": 1}},
        {"name": "Both params", "params": {"page[size]": 10, "page[number]": 1}},
        {"name": "Small page", "params": {"page[size]": 5, "page[number]": 1}},
    ]
    
    for test_case in test_cases:
        print(f"\n🔬 {test_case['name']}: {test_case['params']}")
        
        try:
            response = client.session.get(url, params=test_case['params'])
            
            if response.status_code == 200:
                data = response.json()
                tags = data.get('data', [])
                
                print(f"  ✅ Got {len(tags)} tags")
                
                # Show actual URL that was called
                print(f"  📍 URL: {response.url}")
                
                if len(tags) > 0:
                    first_tag_name = tags[0].get('attributes', {}).get('name', 'N/A')
                    print(f"  🏷️  First tag: '{first_tag_name}'")
                
            else:
                print(f"  ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")


def main():
    print("🐛 NationBuilder API Debug Session")
    print("=" * 60)
    print("Figuring out why we're getting 136k+ tags instead of 6,671")
    print()
    
    client = load_client()
    
    # Debug the raw API call
    debug_raw_api_call(client)
    
    # Test pagination manually
    test_pagination_manually(client)
    
    # Test different parameters
    test_with_correct_parameters(client)
    
    print(f"\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("Check the output above to understand:")
    print("1. What URL we're actually calling")
    print("2. What parameters we're sending") 
    print("3. What response structure we're getting")
    print("4. Whether pagination is working correctly")


if __name__ == "__main__":
    main()