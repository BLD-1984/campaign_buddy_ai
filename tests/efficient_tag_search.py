# tests/efficient_tag_search.py
"""
Efficient search through ~6,500 signup_tags for patterns that begin with given strings
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


def get_all_signup_tags_efficiently(client):
    """Get ALL signup_tags efficiently (should be 6,671 total based on web interface)"""
    print("📋 Getting ALL signup_tags efficiently")
    print("-" * 50)
    
    all_tags = []
    page = 1
    
    try:
        while True:
            result = client.get_signup_tags(page_size=100)
            tags = result.get('data', [])
            
            if not tags:
                print(f"   📄 No more tags at page {page}")
                break
            
            all_tags.extend(tags)
            
            # Progress every 10 pages
            if page % 10 == 0:
                print(f"   📊 Page {page}: {len(all_tags)} tags loaded so far...")
            
            # If we get less than 100, we've reached the end
            if len(tags) < 100:
                print(f"   📄 Reached end at page {page} with {len(tags)} tags")
                break
            
            page += 1
            
            # REMOVE artificial safety limits! Let it get all 6,671 tags
            # The web interface shows exactly 6,671 tags, so let's get them all
        
        print(f"✅ Loaded {len(all_tags)} total signup_tags")
        
        # Debug: Show some sample tag names to verify we're getting the right data
        if len(all_tags) > 0:
            print(f"📋 Sample tag names (first 5):")
            for i, tag in enumerate(all_tags[:5]):
                tag_name = tag.get('attributes', {}).get('name', 'N/A')
                tag_id = tag.get('id')
                print(f"   {i+1}. ID {tag_id}: '{tag_name}'")
        
        return all_tags
        
    except Exception as e:
        print(f"❌ Error loading tags: {e}")
        return []


def search_tags_by_patterns(all_tags, patterns):
    """Search through all tags for patterns that start with given strings"""
    print(f"\n🔍 Searching {len(all_tags)} tags for patterns")
    print("-" * 50)
    
    results = {}
    
    for pattern in patterns:
        print(f"   🎯 Pattern: '{pattern}'")
        matching_tags = []
        
        for tag in all_tags:
            tag_name = tag.get('attributes', {}).get('name', '')
            tag_id = tag.get('id')
            
            # Check if tag name starts with this pattern (case insensitive)
            if tag_name.lower().startswith(pattern.lower()):
                matching_tags.append({
                    'id': tag_id,
                    'name': tag_name
                })
                
                # Show first few matches
                if len(matching_tags) <= 5:
                    print(f"      ✅ ID {tag_id}: '{tag_name}'")
        
        if len(matching_tags) > 5:
            print(f"      ... and {len(matching_tags) - 5} more matches")
        elif len(matching_tags) == 0:
            # Debug: Let's see if there are any tags that CONTAIN this pattern (not just start with)
            containing_tags = []
            for tag in all_tags:
                tag_name = tag.get('attributes', {}).get('name', '')
                if pattern.lower() in tag_name.lower():
                    containing_tags.append(tag_name)
                    if len(containing_tags) <= 3:
                        print(f"      🔍 Contains '{pattern}': '{tag_name}'")
            
            if len(containing_tags) > 3:
                print(f"      ... and {len(containing_tags) - 3} more containing '{pattern}'")
            elif len(containing_tags) == 0:
                print(f"      ❌ No tags even CONTAIN '{pattern}'")
        
        results[pattern] = matching_tags
        print(f"      📊 Total matches (starts with): {len(matching_tags)}")
    
    return results


def search_your_original_patterns(all_tags):
    """Search for your original filter patterns"""
    print(f"\n🎯 Searching for YOUR ORIGINAL filter patterns")
    print("-" * 50)
    
    # Your original patterns from the filter
    original_patterns = [
        "Met at deployment on 2025-07",
        "Met at event on 2025-07", 
        "Met at rally on 2025-07",
        "Met at online on 2025-07",
        "Met at other on 2025-07"
    ]
    
    results = search_tags_by_patterns(all_tags, original_patterns)
    
    # Combine all matching tag IDs
    all_matching_tag_ids = []
    for pattern, matches in results.items():
        for match in matches:
            all_matching_tag_ids.append(match['id'])
    
    return all_matching_tag_ids, results


def debug_met_at_search(all_tags):
    """Debug why we're not finding 'Met at' tags when we know they exist"""
    print(f"\n🐛 DEBUG: Looking for 'Met at' tags manually")
    print("-" * 50)
    
    # We know these specific tags exist from our previous testing
    known_tag_names = [
        'Met at deployment on 2021-07-29—Cinco Ranch TX (Tax Office)',
        'Met at deployment on 2025-07-23—Tracy CA (Post Office)'
    ]
    
    print(f"🔍 Searching for known tags in our {len(all_tags)} loaded tags...")
    
    found_known_tags = []
    met_at_tags = []
    
    for tag in all_tags:
        tag_name = tag.get('attributes', {}).get('name', '')
        tag_id = tag.get('id')
        
        # Check if this is one of our known tags
        if tag_name in known_tag_names:
            found_known_tags.append(tag)
            print(f"   ✅ FOUND KNOWN TAG: ID {tag_id} - '{tag_name}'")
        
        # Check if this is any 'met at' tag
        if 'met at' in tag_name.lower():
            met_at_tags.append(tag)
    
    print(f"\n📊 Results:")
    print(f"   Known tags found: {len(found_known_tags)}/2")
    print(f"   Total 'Met at' tags found: {len(met_at_tags)}")
    
    if len(met_at_tags) > 0:
        print(f"\n🎯 First 10 'Met at' tags found:")
        for i, tag in enumerate(met_at_tags[:10]):
            tag_name = tag.get('attributes', {}).get('name', '')
            tag_id = tag.get('id')
            print(f"   {i+1}. ID {tag_id}: '{tag_name}'")
        
        if len(met_at_tags) > 10:
            print(f"   ... and {len(met_at_tags) - 10} more")
    
    if len(found_known_tags) == 0:
        print(f"\n❌ PROBLEM: We didn't find the known tags!")
        print(f"   This means we're not loading the right tags or there's a pagination issue")
        
        # Show what we DID load
        print(f"\n📋 What we actually loaded (first 10 tags):")
        for i, tag in enumerate(all_tags[:10]):
            tag_name = tag.get('attributes', {}).get('name', '')
            tag_id = tag.get('id')
            print(f"   {i+1}. ID {tag_id}: '{tag_name}'")
    
    return met_at_tags


def test_api_filtering_capabilities(client):
    """Test if the API supports filtering tags by name patterns"""
    print(f"\n🧪 Testing API filtering capabilities")
    print("-" * 50)
    
    test_filters = [
        # Test exact name match
        {'name': 'Met at deployment on 2025-07-23—Tracy CA (Post Office)'},
        
        # Test if prefix filtering works
        {'name': {'prefix': 'Met at deployment on 2025-07'}},
        
        # Test if contains/match filtering works  
        {'name': {'match': 'Met at deployment'}},
        {'name': {'contains': '2025-07'}},
    ]
    
    for i, test_filter in enumerate(test_filters, 1):
        print(f"   Test {i}: {test_filter}")
        
        try:
            result = client.get_signup_tags(filters=test_filter, page_size=10)
            tags = result.get('data', [])
            
            if tags:
                print(f"      ✅ SUCCESS: Found {len(tags)} tags")
                for tag in tags[:3]:  # Show first 3
                    tag_name = tag.get('attributes', {}).get('name', 'N/A')
                    print(f"         - {tag_name}")
            else:
                print(f"      ❌ No results")
                
        except Exception as e:
            print(f"      ❌ Failed: {e}")


def main():
    print("🔍 Efficient Tag Search for Pattern Matching")
    print("=" * 60)
    print("Searching through ~6,500 signup_tags for your filter patterns")
    print()
    
    client = load_client()
    
    # Test API filtering first
    test_api_filtering_capabilities(client)
    
    # Get all tags
    all_tags = get_all_signup_tags_efficiently(client)
    
    if not all_tags:
        print("❌ Could not load tags")
        return
    
    # Search for your original patterns
    original_tag_ids, original_results = search_your_original_patterns(all_tags)
    
    # Debug the Met at search
    debug_met_at_tags = debug_met_at_search(all_tags)
    
    print(f"\n" + "=" * 60)
    print("🎯 FINAL SUMMARY:")
    
    if original_tag_ids:
        print(f"✅ Found {len(original_tag_ids)} tags matching your ORIGINAL filter patterns!")
        print(f"🎯 Tag IDs for complex filter: {original_tag_ids}")
        
        print(f"\n📋 Breakdown by original pattern:")
        for pattern, matches in original_results.items():
            if matches:
                print(f"   '{pattern}': {len(matches)} tags")
                for match in matches[:3]:
                    print(f"      - ID {match['id']}: {match['name']}")
                if len(matches) > 3:
                    print(f"      - ... and {len(matches) - 3} more")
    else:
        print(f"⚠️  No tags found matching your exact original patterns")
        
        # Show what debug found
        if debug_met_at_tags:
            print(f"🔍 But debug found {len(debug_met_at_tags)} 'Met at' tags total")
            print(f"💡 This suggests the patterns need to be adjusted")
            
            # Show some examples of what actually exists
            print(f"\n📋 Examples of actual 'Met at' tag patterns:")
            for tag in debug_met_at_tags[:5]:
                print(f"   - {tag.get('attributes', {}).get('name', 'N/A')}")
        else:
            print(f"❌ Debug found no 'Met at' tags either - there might be a loading issue")
    
    print(f"\n💡 NEXT STEPS:")
    if original_tag_ids:
        print(f"✅ Use these {len(original_tag_ids)} tag IDs in your complex filter")
        print(f"📋 Tag IDs: {original_tag_ids}")
    elif debug_met_at_tags:
        print(f"🔧 Adjust your search patterns based on what actually exists")
        print(f"📋 Found {len(debug_met_at_tags)} 'Met at' tags with different patterns")
        
        # Suggest some tag IDs to use
        deployment_tags = [tag for tag in debug_met_at_tags if 'deployment' in tag.get('attributes', {}).get('name', '').lower()]
        if deployment_tags:
            tag_ids = [tag.get('id') for tag in deployment_tags[:10]]
            print(f"🎯 Suggested tag IDs for testing: {tag_ids}")
    else:
        print(f"🚨 No 'Met at' tags found - check if all {len(all_tags)} tags were loaded correctly")
        print(f"Expected: 6,671 tags. Got: {len(all_tags)} tags")


if __name__ == "__main__":
    main()