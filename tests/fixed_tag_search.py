# tests/fixed_tag_search.py
"""
Fixed tag search using PROPER NationBuilder pagination
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


def get_all_signup_tags_correctly(client):
    """Get ALL signup_tags using PROPER NationBuilder pagination"""
    print("📋 Getting ALL signup_tags using PROPER pagination")
    print("-" * 50)
    
    all_tags = []
    page_num = 1
    
    # Start with first page
    url = f"{client.base_url}/signup_tags"
    params = {'page[size]': 100}
    
    try:
        while True:
            print(f"   📄 Loading page {page_num}...")
            
            response = client.session.get(url, params=params)
            
            if response.status_code != 200:
                print(f"   ❌ API error {response.status_code}: {response.text}")
                break
            
            data = response.json()
            tags = data.get('data', [])
            
            if not tags:
                print(f"   📄 No more tags at page {page_num}")
                break
            
            all_tags.extend(tags)
            
            # Show progress
            if len(tags) > 0:
                first_id = tags[0].get('id')
                last_id = tags[-1].get('id')
                print(f"      ✅ Got {len(tags)} tags (IDs {first_id}-{last_id}), total: {len(all_tags)}")
            
            # Check for next page using the links provided by the API
            links = data.get('links', {})
            next_link = links.get('next')
            
            if not next_link:
                print(f"   📄 No next link - reached end at page {page_num}")
                break
            
            # Use the next link provided by the API
            # Convert relative URL to full URL if needed
            if next_link.startswith('/'):
                url = f"https://{client.nation_slug}.nationbuilder.com{next_link}"
                params = {}  # Parameters are already in the URL
            else:
                url = next_link
                params = {}
            
            page_num += 1
            
            # Safety check - should be around 67 pages for 6,671 tags
            if page_num > 100:
                print(f"   ⚠️  Safety check: page {page_num} seems too high for 6,671 tags")
                break
        
        print(f"✅ Loaded {len(all_tags)} total signup_tags using proper pagination")
        return all_tags
        
    except Exception as e:
        print(f"❌ Error loading tags: {e}")
        return []


def find_met_at_tags(all_tags):
    """Find all 'Met at' tags in the loaded data"""
    print(f"\n🔍 Searching {len(all_tags)} tags for 'Met at' patterns")
    print("-" * 50)
    
    met_at_tags = []
    
    for tag in all_tags:
        tag_name = tag.get('attributes', {}).get('name', '')
        tag_id = tag.get('id')
        
        if 'met at' in tag_name.lower():
            met_at_tags.append({
                'id': tag_id,
                'name': tag_name
            })
    
    print(f"✅ Found {len(met_at_tags)} 'Met at' tags")
    
    # Group by type
    by_type = {
        'deployment': [],
        'event': [],
        'rally': [],
        'online': [],
        'other': []
    }
    
    for tag in met_at_tags:
        tag_name = tag['name'].lower()
        categorized = False
        
        for tag_type in by_type.keys():
            if tag_type in tag_name:
                by_type[tag_type].append(tag)
                categorized = True
                break
        
        if not categorized:
            by_type['other'].append(tag)
    
    print(f"\n📊 Breakdown by type:")
    for tag_type, tags in by_type.items():
        if tags:
            print(f"   {tag_type}: {len(tags)} tags")
            
            # Show 2025-07 tags specifically
            july_2025_tags = [t for t in tags if '2025-07' in t['name']]
            if july_2025_tags:
                print(f"      🎯 2025-07 {tag_type} tags:")
                for tag in july_2025_tags:
                    print(f"         ID {tag['id']}: {tag['name']}")
    
    return met_at_tags


def find_original_filter_patterns(all_tags):
    """Find tags matching the original filter patterns"""
    print(f"\n🎯 Finding tags for ORIGINAL filter patterns")
    print("-" * 50)
    
    # Original patterns from your filter
    patterns = [
        "Met at deployment on 2025-07",
        "Met at event on 2025-07", 
        "Met at rally on 2025-07",
        "Met at online on 2025-07",
        "Met at other on 2025-07"
    ]
    
    matching_tag_ids = []
    
    for pattern in patterns:
        print(f"   🔍 Pattern: '{pattern}'")
        matches = []
        
        for tag in all_tags:
            tag_name = tag.get('attributes', {}).get('name', '')
            tag_id = tag.get('id')
            
            if tag_name.lower().startswith(pattern.lower()):
                matches.append(tag)
                matching_tag_ids.append(tag_id)
                print(f"      ✅ ID {tag_id}: '{tag_name}'")
        
        if not matches:
            print(f"      ❌ No matches for this pattern")
    
    print(f"\n🎯 TOTAL: Found {len(matching_tag_ids)} tags matching original patterns")
    if matching_tag_ids:
        print(f"📋 Tag IDs for complex filter: {matching_tag_ids}")
    
    return matching_tag_ids


def main():
    print("🔧 FIXED Tag Search with Proper Pagination")
    print("=" * 60)
    print("Using the 'next' links provided by the NationBuilder API")
    print()
    
    client = load_client()
    
    # Get all tags using proper pagination
    all_tags = get_all_signup_tags_correctly(client)
    
    if not all_tags:
        print("❌ Could not load tags")
        return
    
    print(f"\n🎯 Expected: 6,671 tags. Got: {len(all_tags)} tags")
    
    if len(all_tags) != 6671:
        print(f"⚠️  Tag count doesn't match web interface - but let's continue...")
    
    # Find all Met at tags
    met_at_tags = find_met_at_tags(all_tags)
    
    # Find tags matching original filter
    original_filter_tag_ids = find_original_filter_patterns(all_tags)
    
    print(f"\n" + "=" * 60)
    print("🎉 FINAL RESULTS:")
    
    if original_filter_tag_ids:
        print(f"✅ SUCCESS! Found {len(original_filter_tag_ids)} tags for your complex filter!")
        print(f"🎯 Use these tag IDs: {original_filter_tag_ids}")
        print(f"📋 Ready to build the working complex filter!")
    else:
        print(f"⚠️  No exact matches for original patterns")
        if met_at_tags:
            print(f"🔍 But found {len(met_at_tags)} 'Met at' tags with different patterns")
            print(f"💡 Consider adjusting your filter patterns")


if __name__ == "__main__":
    main()