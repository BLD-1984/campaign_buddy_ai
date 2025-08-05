# targeted_exploration.py
"""
Targeted exploration to understand the specific filter criteria
"""

import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append('src')
from nb_api_client import NationBuilderClient
import os


def load_client():
    return NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )


def explore_tags_structure(client):
    """Understand how tags work in the API"""
    print("🏷️  Understanding Tags Structure")
    print("=" * 50)
    
    try:
        # Try to get tags directly
        print("🔍 Attempting to get tags endpoint...")
        response = client.session.get(f"{client.base_url}/tags")
        
        if response.status_code == 200:
            tags_data = response.json()
            tags = tags_data.get('data', [])
            print(f"✅ Found {len(tags)} total tags")
            
            # Look for "Met at" tags
            met_at_tags = []
            for tag in tags:
                tag_name = tag.get('attributes', {}).get('name', '')
                if tag_name.lower().startswith('met at'):
                    met_at_tags.append(tag)
                    
            print(f"🎯 Found {len(met_at_tags)} 'Met at' tags:")
            for tag in met_at_tags[:10]:  # Show first 10
                tag_name = tag.get('attributes', {}).get('name', 'N/A')
                tag_id = tag.get('id')
                print(f"   Tag {tag_id}: {tag_name}")
                
            return met_at_tags
            
        else:
            print(f"❌ Tags endpoint returned {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting tags: {e}")
    
    return []


def check_path_1111_details(client):
    """Get details about path 1111 (the target path)"""
    print("\n🛤️  Path 1111 Details")
    print("=" * 50)
    
    try:
        # Get all paths to find 1111
        paths = client.get_paths().get('data', [])
        target_path = None
        
        for path in paths:
            if path.get('id') == '1111':
                target_path = path
                break
                
        if target_path:
            attrs = target_path.get('attributes', {})
            print(f"✅ Found Path 1111: {attrs.get('name', 'N/A')}")
            
            # Get steps for this path
            steps = client.get_path_steps('1111').get('data', [])
            print(f"📋 Path 1111 has {len(steps)} steps:")
            
            for step in steps:
                step_id = step.get('id')
                step_name = step.get('attributes', {}).get('name', 'N/A')
                is_target_step = step_id in ['1393', '1394']
                marker = " ⚠️  (EXCLUSION STEP)" if is_target_step else ""
                print(f"   Step {step_id}: {step_name}{marker}")
                
            return steps[0] if steps else None  # Return first step for assignment
            
        else:
            print("❌ Path 1111 not found")
            
    except Exception as e:
        print(f"❌ Error getting path 1111: {e}")
        
    return None


def test_path_journey_queries(client):
    """Test how to query path journeys for completion/abandonment status"""
    print("\n🚶 Testing Path Journey Queries")
    print("=" * 50)
    
    try:
        # Get some path journeys to understand the structure
        print("🔍 Getting sample path journeys...")
        
        # Try to get path journeys for path 1111
        url = f"{client.base_url}/path_journeys"
        params = {'filter[path_id]': '1111', 'page[size]': 10}
        
        response = client.session.get(url, params=params)
        if response.status_code == 200:
            journeys_data = response.json()
            journeys = journeys_data.get('data', [])
            print(f"✅ Found {len(journeys)} journeys for path 1111")
            
            # Show sample journey structure
            for i, journey in enumerate(journeys[:3]):
                attrs = journey.get('attributes', {})
                print(f"\n📋 Journey {i+1}:")
                print(f"   ID: {journey.get('id')}")
                print(f"   Signup ID: {attrs.get('signup_id')}")
                print(f"   Path Step ID: {attrs.get('path_step_id')}")
                print(f"   Status: {attrs.get('status')}")
                print(f"   Created: {attrs.get('created_at')}")
                
                # This tells us what statuses exist
                status = attrs.get('status')
                if status:
                    print(f"   ✅ Status values we can filter on: '{status}'")
                    
        else:
            print(f"❌ Path journeys query failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing path journeys: {e}")


def test_signup_filtering_by_tags(client):
    """Test how to filter signups by tags"""
    print("\n🔍 Testing Signup Filtering by Tags")
    print("=" * 50)
    
    try:
        # Test different tag filtering approaches
        print("🧪 Testing tag filtering methods...")
        
        # Method 1: Try to filter by tag name using taggings
        print("\n1. Filtering via taggings relationship:")
        try:
            result = client.get_signups(
                filters={'taggings': {'tag_name': 'Met at'}},  # This might not work
                fields=['first_name', 'last_name'],
                page_size=5
            )
            signups = result.get('data', [])
            print(f"   Found {len(signups)} signups")
        except Exception as e:
            print(f"   ❌ Method 1 failed: {e}")
        
        # Method 2: Get signups with taggings included and filter manually
        print("\n2. Getting signups with taggings included:")
        try:
            result = client.get_signups(
                include=['taggings'],
                fields=['first_name', 'last_name'],
                page_size=10
            )
            
            signups = result.get('data', [])
            included = result.get('included', [])
            
            print(f"   Got {len(signups)} signups with {len(included)} included items")
            
            # Look at taggings structure
            taggings = [item for item in included if item.get('type') == 'taggings']
            print(f"   Found {len(taggings)} tagging records")
            
            if taggings:
                sample_tagging = taggings[0]
                print(f"   Sample tagging: {sample_tagging.get('attributes', {})}")
                
        except Exception as e:
            print(f"   ❌ Method 2 failed: {e}")
            
    except Exception as e:
        print(f"❌ Error testing tag filtering: {e}")


def main():
    print("🎯 Targeted Exploration for Filter Criteria")
    print("=" * 60)
    
    client = load_client()
    
    # Run targeted explorations
    met_at_tags = explore_tags_structure(client)
    first_step = check_path_1111_details(client)
    test_path_journey_queries(client)
    test_signup_filtering_by_tags(client)
    
    print("\n" + "=" * 60)
    print("🎯 Key Information for Filter:")
    print(f"📍 Met at tags found: {len(met_at_tags) if met_at_tags else 'Need to check'}")
    print(f"📍 Path 1111 first step: {first_step.get('id') if first_step else 'Need to check'}")
    print("📍 Ready to build the complex filter!")


if __name__ == "__main__":
    main()