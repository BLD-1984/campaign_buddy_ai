# tests/direct_tag_approach.py
"""
Use the known tag IDs and look for similar ones in that range
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


def look_around_known_tag_ids(client):
    """Look for tags around the known IDs 3482 and 14732"""
    print("🎯 Looking around known tag IDs for similar tags")
    print("-" * 50)
    
    known_tag_ids = [3482, 14732]  # The ones we found
    met_at_tags = []
    
    for base_id in known_tag_ids:
        print(f"\n🔍 Checking around tag ID {base_id}:")
        
        # Check a range around this ID
        start_id = max(1, base_id - 50)
        end_id = base_id + 100
        
        for tag_id in range(start_id, end_id):
            try:
                # Try to get this specific tag
                response = client.session.get(f"{client.base_url}/signup_tags/{tag_id}")
                
                if response.status_code == 200:
                    tag_data = response.json()
                    tag = tag_data.get('data', {})
                    tag_name = tag.get('attributes', {}).get('name', '')
                    
                    # Check if it's a "Met at" tag
                    if 'met at' in tag_name.lower():
                        met_at_tags.append({
                            'id': str(tag_id),
                            'name': tag_name
                        })
                        print(f"   🎯 FOUND: ID {tag_id} - '{tag_name}'")
                        
                        # Check specifically for 2025-07
                        if '2025-07' in tag_name:
                            print(f"      ⭐ THIS IS A 2025-07 TAG!")
                
            except Exception:
                continue  # Tag doesn't exist, skip
        
        print(f"   Checked range {start_id}-{end_id}")
    
    return met_at_tags


def search_high_id_ranges(client):
    """Search in higher ID ranges where newer tags might be"""
    print(f"\n🔍 Searching high ID ranges for newer tags")
    print("-" * 50)
    
    # Since 14732 was found, newer 2025 tags might be in ranges around there
    high_ranges = [
        (14700, 14800),  # Around the known 2025 tag
        (15000, 15100),  # Slightly higher
        (16000, 16100),  # Even higher
        (20000, 20100),  # Much higher
    ]
    
    met_at_tags = []
    
    for start_id, end_id in high_ranges:
        print(f"   Checking range {start_id}-{end_id}...")
        found_in_range = 0
        
        for tag_id in range(start_id, end_id):
            try:
                response = client.session.get(f"{client.base_url}/signup_tags/{tag_id}")
                
                if response.status_code == 200:
                    tag_data = response.json()
                    tag = tag_data.get('data', {})
                    tag_name = tag.get('attributes', {}).get('name', '')
                    
                    if 'met at' in tag_name.lower():
                        met_at_tags.append({
                            'id': str(tag_id),
                            'name': tag_name
                        })
                        found_in_range += 1
                        
                        if found_in_range <= 3:  # Show first 3 per range
                            print(f"      🎯 ID {tag_id}: '{tag_name}'")
                        
                        if '2025-07' in tag_name:
                            print(f"         ⭐ 2025-07 TAG!")
                
            except Exception:
                continue
        
        if found_in_range > 3:
            print(f"      ... and {found_in_range - 3} more in this range")
        elif found_in_range == 0:
            print(f"      No 'Met at' tags in this range")
    
    return met_at_tags


def use_known_tags_directly(client):
    """Use the tags we already know exist"""
    print(f"\n💡 Using known tag IDs directly")
    print("-" * 50)
    
    # We know these exist
    known_met_at_tags = [
        {'id': '3482', 'name': 'Met at deployment on 2021-07-29—Cinco Ranch TX (Tax Office)'},
        {'id': '14732', 'name': 'Met at deployment on 2025-07-23—Tracy CA (Post Office)'}
    ]
    
    for tag in known_met_at_tags:
        print(f"   ✅ Known tag: ID {tag['id']} - '{tag['name']}'")
        
        # Check how many people have this tag
        try:
            result = client.get_signup_taggings(
                filters={'tag_id': tag['id']},
                page_size=1  # Just get count
            )
            
            # Try to get a second page to see if there are more
            result2 = client.get_signup_taggings(
                filters={'tag_id': tag['id']},
                page_size=100
            )
            
            count = len(result2.get('data', []))
            if count == 100:
                # There might be more, let's get a rough estimate
                print(f"      Has 100+ people (probably more)")
            else:
                print(f"      Has {count} people")
                
        except Exception as e:
            print(f"      Could not count people: {e}")
    
    return known_met_at_tags


def main():
    print("🔍 Direct Tag ID Search Strategy")
    print("=" * 60)
    
    client = load_client()
    
    # Strategy 1: Look around known IDs
    nearby_tags = look_around_known_tag_ids(client)
    
    # Strategy 2: Search high ID ranges
    high_range_tags = search_high_id_ranges(client)
    
    # Strategy 3: Use what we know
    known_tags = use_known_tags_directly(client)
    
    # Combine all found tags
    all_found_tags = nearby_tags + high_range_tags + known_tags
    
    # Remove duplicates
    unique_tags = {}
    for tag in all_found_tags:
        tag_id = tag['id']
        if tag_id not in unique_tags:
            unique_tags[tag_id] = tag
    
    print(f"\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print(f"Found {len(unique_tags)} unique 'Met at' tags total")
    
    # Filter for 2025-07 tags specifically
    july_2025_tags = []
    for tag_id, tag in unique_tags.items():
        if '2025-07' in tag['name']:
            july_2025_tags.append(tag)
    
    if july_2025_tags:
        print(f"\n⭐ Found {len(july_2025_tags)} tags matching '2025-07' pattern:")
        for tag in july_2025_tags:
            print(f"   ID {tag['id']}: '{tag['name']}'")
        
        print(f"\n🎯 RECOMMENDATION:")
        print(f"Use these tag IDs in your complex filter:")
        tag_ids = [tag['id'] for tag in july_2025_tags]
        print(f"Tag IDs: {tag_ids}")
        
    else:
        print(f"\n⚠️  No 2025-07 tags found yet")
        print(f"Consider using all 'Met at deployment' tags for testing:")
        deployment_tags = [tag for tag in unique_tags.values() if 'deployment' in tag['name'].lower()]
        for tag in deployment_tags[:5]:
            print(f"   ID {tag['id']}: '{tag['name']}'")


if __name__ == "__main__":
    main()
    