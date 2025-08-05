# examine_specific_person.py
"""
Examine a specific person (655029) to see how their "Met at deployment" tags 
appear in the API response
"""

import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append('src')
from nb_api_client import NationBuilderClient
import os
import json


def load_client():
    return NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )


def examine_person_thoroughly(client, signup_id):
    """Examine a specific person with all possible tag relationships"""
    print(f"🔍 Examining Signup ID: {signup_id}")
    print("-" * 50)
    
    try:
        # Get the person with ALL possible includes
        result = client.get_signup_by_id(
            signup_id,
            fields=['first_name', 'last_name', 'email', 'id'],
            include=['signup_tags', 'taggings']
        )
        
        print("📋 Basic Info:")
        signup = result.get('data', {})
        attrs = signup.get('attributes', {})
        name = f"{attrs.get('first_name', 'N/A')} {attrs.get('last_name', 'N/A')}"
        email = attrs.get('email', 'N/A')
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        print(f"   ID: {signup.get('id')}")
        
        print(f"\n🔗 Relationships:")
        relationships = signup.get('relationships', {})
        for rel_name, rel_data in relationships.items():
            if 'tag' in rel_name.lower():
                print(f"   {rel_name}: {rel_data}")
        
        print(f"\n📦 Included Data:")
        included = result.get('included', [])
        print(f"   Total included items: {len(included)}")
        
        # Group included items by type
        by_type = {}
        for item in included:
            item_type = item.get('type', 'unknown')
            if item_type not in by_type:
                by_type[item_type] = []
            by_type[item_type].append(item)
        
        print(f"   Types found: {list(by_type.keys())}")
        
        # Look at tag-related included items
        tag_items = []
        for item_type, items in by_type.items():
            if 'tag' in item_type.lower():
                print(f"\n   🏷️  {item_type} ({len(items)} items):")
                for item in items:
                    attrs = item.get('attributes', {})
                    tag_name = attrs.get('name') or attrs.get('tag_name', 'N/A')
                    tag_id = item.get('id')
                    
                    print(f"      ID {tag_id}: '{tag_name}'")
                    
                    # Check if this is a "Met at deployment" tag
                    if 'met at deployment' in tag_name.lower():
                        print(f"         🎯 FOUND MET AT DEPLOYMENT TAG!")
                        tag_items.append(item)
        
        return tag_items
        
    except Exception as e:
        print(f"❌ Error examining person: {e}")
        return []


def get_person_via_taggings(client, signup_id):
    """Try to find this person's tags via the signup_taggings endpoint"""
    print(f"\n🔍 Finding tags via signup_taggings endpoint")
    print("-" * 50)
    
    try:
        # Get all taggings for this specific signup
        result = client.get_signup_taggings(
            filters={'signup_id': signup_id},
            include=['tag'],  # Include the actual tag data
            page_size=100
        )
        
        taggings = result.get('data', [])
        included = result.get('included', [])
        
        print(f"   Found {len(taggings)} taggings for this person")
        print(f"   Found {len(included)} included tag records")
        
        met_at_tags = []
        
        # Look at the included tag data
        for item in included:
            if item.get('type') == 'signup_tags':
                tag_name = item.get('attributes', {}).get('name', '')
                tag_id = item.get('id')
                
                print(f"   Tag ID {tag_id}: '{tag_name}'")
                
                if 'met at deployment' in tag_name.lower():
                    print(f"      🎯 FOUND MET AT DEPLOYMENT TAG!")
                    met_at_tags.append(item)
        
        return met_at_tags
        
    except Exception as e:
        print(f"❌ Error getting taggings: {e}")
        return []


def try_direct_tag_lookup(client, tag_ids):
    """Try to look up specific tags directly"""
    print(f"\n🔍 Looking up tags directly")
    print("-" * 50)
    
    for tag_id in tag_ids:
        try:
            # Try to get the tag directly
            response = client.session.get(f"{client.base_url}/signup_tags/{tag_id}")
            if response.status_code == 200:
                tag_data = response.json()
                tag = tag_data.get('data', {})
                tag_name = tag.get('attributes', {}).get('name', 'N/A')
                print(f"   Direct lookup Tag ID {tag_id}: '{tag_name}'")
            else:
                print(f"   ❌ Could not look up tag {tag_id}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error looking up tag {tag_id}: {e}")


def main():
    print("🕵️ Investigating Specific Person's Tags")
    print("=" * 60)
    
    client = load_client()
    
    # Check both people
    people_to_check = [
        {"id": "655029", "description": "Person with 2021 'Met at deployment' tag"},
        {"id": "718187", "description": "Person with 2025-07 'Met at deployment' tag"}
    ]
    
    all_found_tags = {}
    
    for person in people_to_check:
        signup_id = person["id"]
        description = person["description"]
        
        print(f"\n{'='*60}")
        print(f"🔍 EXAMINING: {description}")
        print(f"Signup ID: {signup_id}")
        
        # Method 1: Get person with includes
        print(f"\nMETHOD 1: Get person with tag includes")
        met_at_tags_1 = examine_person_thoroughly(client, signup_id)
        
        # Method 2: Get via signup_taggings
        print(f"\nMETHOD 2: Get via signup_taggings endpoint")
        met_at_tags_2 = get_person_via_taggings(client, signup_id)
        
        # Collect unique tags for this person
        person_tags = {}
        for tag_list in [met_at_tags_1, met_at_tags_2]:
            for tag in tag_list:
                tag_id = tag.get('id')
                if tag_id:
                    person_tags[tag_id] = tag
        
        all_found_tags[signup_id] = {
            'person': person,
            'tags': person_tags
        }
        
        print(f"\n📋 SUMMARY for {signup_id}:")
        if person_tags:
            print(f"✅ Found {len(person_tags)} 'Met at deployment' tags:")
            for tag_id, tag in person_tags.items():
                tag_name = tag.get('attributes', {}).get('name', 'N/A')
                print(f"   ID {tag_id}: '{tag_name}'")
        else:
            print("❌ No 'Met at deployment' tags found")
    
    # Overall Summary
    print("\n" + "=" * 60)
    print("🎯 OVERALL SUMMARY:")
    
    all_unique_tags = {}
    for person_data in all_found_tags.values():
        for tag_id, tag in person_data['tags'].items():
            all_unique_tags[tag_id] = tag
    
    if all_unique_tags:
        print(f"✅ Found {len(all_unique_tags)} unique 'Met at deployment' tags total:")
        
        tags_2021 = []
        tags_2025 = []
        tags_other = []
        
        for tag_id, tag in all_unique_tags.items():
            tag_name = tag.get('attributes', {}).get('name', '')
            print(f"   ID {tag_id}: '{tag_name}'")
            
            if '2021' in tag_name:
                tags_2021.append((tag_id, tag_name))
            elif '2025' in tag_name:
                tags_2025.append((tag_id, tag_name))
            else:
                tags_other.append((tag_id, tag_name))
        
        print(f"\n📊 Breakdown:")
        print(f"   2021 tags: {len(tags_2021)}")
        print(f"   2025 tags: {len(tags_2025)}")
        print(f"   Other: {len(tags_other)}")
        
        if tags_2025:
            print(f"\n🎯 2025 TAGS FOUND:")
            for tag_id, tag_name in tags_2025:
                print(f"   ID {tag_id}: '{tag_name}'")
            print(f"\n✅ These 2025 tags can be used in your complex filter!")
        else:
            print(f"\n⚠️  No 2025 tags found yet")
            print(f"   The 2025-07 tags from your filter may not exist yet")
        
    else:
        print("❌ No 'Met at deployment' tags found for either person")
        print("🤔 This suggests an API access issue")
    
    print(f"\n💡 Next step: Use the found tag IDs to build the working complex filter!")


if __name__ == "__main__":
    main()