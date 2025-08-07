# tag_debug.py
"""
Debug tag searching to see why 'zi-c-24h' isn't found
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from nb_api_client import NationBuilderClient

def debug_tag_search():
    """Debug tag searching to understand why 'zi-c-24h' isn't found"""
    
    print("🏷️  TAG SEARCH DEBUG")
    print("=" * 25)
    
    # Initialize client
    client = NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )
    
    # Search for tags that might match
    search_terms = ["zi-c-24h", "zi", "c-24h", "24h"]
    
    print(f"🔍 Searching for tags containing these terms:")
    for term in search_terms:
        print(f"   - '{term}'")
    
    print(f"\n📋 GETTING ALL TAGS (first 500)...")
    
    try:
        all_tags = []
        page = 1
        
        while len(all_tags) < 500:  # Limit for debugging
            result = client.get_signup_tags(page_size=100)
            tags = result.get('data', [])
            
            if not tags:
                break
                
            all_tags.extend(tags)
            print(f"   Page {page}: Found {len(tags)} tags, total so far: {len(all_tags)}")
            
            if len(tags) < 100:
                break
                
            page += 1
            if page > 5:  # Safety limit for debugging
                break
        
        print(f"\n📊 Total tags retrieved: {len(all_tags)}")
        
        # Look for our specific tag and similar ones
        print(f"\n🎯 SEARCHING FOR TARGET TAGS:")
        
        matching_tags = []
        exact_match = None
        
        for tag in all_tags:
            tag_attrs = tag.get('attributes', {})
            tag_name = tag_attrs.get('name', '')
            tag_id = tag.get('id')
            
            # Check for exact match
            if tag_name == 'zi-c-24h':
                exact_match = (tag_id, tag_name)
                matching_tags.append((tag_id, tag_name, "EXACT"))
                
            # Check for partial matches with any search term
            elif any(term.lower() in tag_name.lower() for term in search_terms):
                matching_tags.append((tag_id, tag_name, "PARTIAL"))
        
        # Show results
        if exact_match:
            print(f"✅ FOUND EXACT MATCH:")
            print(f"   ID: {exact_match[0]}")
            print(f"   Name: '{exact_match[1]}'")
        else:
            print(f"❌ NO EXACT MATCH for 'zi-c-24h'")
        
        if matching_tags:
            print(f"\n🔍 SIMILAR TAGS FOUND:")
            for tag_id, tag_name, match_type in matching_tags[:10]:  # Show first 10
                print(f"   ID: {tag_id} | Name: '{tag_name}' | Match: {match_type}")
        else:
            print(f"\n❌ NO SIMILAR TAGS FOUND")
        
        # Check if tag ID 14890 exists
        print(f"\n🎯 CHECKING TAG ID 14890:")
        tag_14890 = None
        for tag in all_tags:
            if tag.get('id') == '14890':
                tag_14890 = tag
                break
        
        if tag_14890:
            attrs = tag_14890.get('attributes', {})
            print(f"✅ FOUND TAG ID 14890:")
            print(f"   Name: '{attrs.get('name', 'No name')}'")
            print(f"   Description: '{attrs.get('description', 'No description')}'")
        else:
            print(f"❌ TAG ID 14890 NOT FOUND in first {len(all_tags)} tags")
            print(f"   (May need to search more pages)")
        
        # Show a sample of all tag names for reference
        print(f"\n📋 SAMPLE TAG NAMES (first 20):")
        for i, tag in enumerate(all_tags[:20]):
            attrs = tag.get('attributes', {})
            tag_name = attrs.get('name', 'No name')
            tag_id = tag.get('id')
            print(f"   {i+1:2d}. ID: {tag_id} | Name: '{tag_name}'")
        
        return matching_tags, exact_match, tag_14890
        
    except Exception as e:
        print(f"❌ Error searching tags: {e}")
        return [], None, None

def test_tag_by_id():
    """Test finding people with tag ID 14890 directly"""
    
    print(f"\n🧪 TESTING TAG ID 14890 DIRECTLY")
    print("=" * 35)
    
    client = NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )
    
    try:
        # Get signup_taggings for tag ID 14890
        print(f"🔍 Getting signup_taggings for tag ID 14890...")
        
        result = client.get_signup_taggings(
            filters={'tag_id': '14890'}, 
            page_size=10  # Just get first 10 for testing
        )
        
        taggings = result.get('data', [])
        print(f"📊 Found {len(taggings)} taggings for tag ID 14890")
        
        if taggings:
            print(f"✅ SUCCESS! People found with tag ID 14890:")
            
            signup_ids = set()
            for i, tagging in enumerate(taggings[:5], 1):  # Show first 5
                attrs = tagging.get('attributes', {})
                signup_id = attrs.get('signup_id')
                tag_id = attrs.get('tag_id')
                print(f"   {i}. Signup ID: {signup_id}, Tag ID: {tag_id}")
                if signup_id:
                    signup_ids.add(str(signup_id))
            
            print(f"\n📋 Unique signup IDs: {len(signup_ids)}")
            print(f"✅ Tag ID 14890 approach WORKS!")
            
            return True
        else:
            print(f"❌ No taggings found for tag ID 14890")
            print(f"   This might mean:")
            print(f"   - No one is currently tagged with this tag")
            print(f"   - The tag ID is incorrect")
            print(f"   - API permission issues")
            
            return False
        
    except Exception as e:
        print(f"❌ Error testing tag ID: {e}")
        return False

if __name__ == "__main__":
    # Debug tag search
    matching_tags, exact_match, tag_14890 = debug_tag_search()
    
    # Test tag ID approach
    tag_id_works = test_tag_by_id()
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print("=" * 20)
    
    if exact_match:
        print(f"✅ Use tag name approach - exact match found")
    elif tag_id_works:
        print(f"✅ Use tag ID approach - tag ID 14890 works")
        print(f"💡 Tag ID is more reliable than tag name")
    else:
        print(f"❌ Neither approach found results")
        print(f"💡 Double-check the tag exists and has people tagged")