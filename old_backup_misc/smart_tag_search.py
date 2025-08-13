# smart_tag_search.py
"""
Smart search for specific tag patterns without downloading 22k+ tags
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


def search_for_met_at_tags_smartly(client):
    """
    Search for 'Met at' tags more efficiently by searching page by page
    and stopping when we find what we're looking for
    """
    print("🎯 Smart Search for 'Met at...' Tags")
    print("-" * 50)
    
    target_patterns = [
        "Met at deployment on 2025-07",
        "Met at event on 2025-07", 
        "Met at rally on 2025-07",
        "Met at online on 2025-07",
        "Met at other on 2025-07"
    ]
    
    found_tags = []
    met_at_variations = []
    july_2025_tags = []
    
    page = 1
    total_searched = 0
    
    try:
        while page <= 300:  # Search up to 30,000 tags
            result = client.get_signup_tags(page_size=100)
            tags = result.get('data', [])
            
            if not tags:
                print(f"   📄 No more tags found at page {page}")
                break
            
            total_searched += len(tags)
            
            # Search this page for our patterns
            page_matches = 0
            for tag in tags:
                tag_name = tag.get('attributes', {}).get('name', '')
                tag_id = tag.get('id')
                
                # Check for exact matches
                if tag_name in target_patterns:
                    found_tags.append({'id': tag_id, 'name': tag_name})
                    print(f"   🎯 EXACT MATCH: '{tag_name}' (ID: {tag_id})")
                    page_matches += 1
                
                # Check for similar "Met at" patterns
                elif tag_name.lower().startswith('met at'):
                    met_at_variations.append({'id': tag_id, 'name': tag_name})
                    print(f"   🔍 MET AT VARIATION: '{tag_name}' (ID: {tag_id})")
                    page_matches += 1
                
                # Check for July 2025 patterns
                elif '2025-07' in tag_name or 'july 2025' in tag_name.lower():
                    july_2025_tags.append({'id': tag_id, 'name': tag_name})
                    if len(july_2025_tags) <= 5:  # Only show first 5
                        print(f"   📅 JULY 2025: '{tag_name}' (ID: {tag_id})")
            
            # Progress update
            if page % 10 == 0:
                print(f"   📊 Page {page}: Searched {total_searched} tags total, found {len(found_tags)} exact matches")
            
            # If we found all 5 target patterns, we can stop
            if len(found_tags) >= 5:
                print(f"   ✅ Found all target patterns! Stopping search.")
                break
            
            # Check if we need more pages
            if len(tags) < 100:
                print(f"   📄 Reached end of tags at page {page}")
                break
                
            page += 1
    
    except Exception as e:
        print(f"❌ Error during search: {e}")
    
    print(f"\n📊 SEARCH RESULTS:")
    print(f"   Total tags searched: {total_searched}")
    print(f"   Exact matches found: {len(found_tags)}")
    print(f"   'Met at' variations: {len(met_at_variations)}")
    print(f"   July 2025 tags: {len(july_2025_tags)}")
    
    return {
        'exact_matches': found_tags,
        'met_at_variations': met_at_variations,
        'july_2025_tags': july_2025_tags,
        'total_searched': total_searched
    }


def try_direct_tag_search(client):
    """
    Try to search for tags using potential filter capabilities
    """
    print(f"\n🔍 Trying Direct Tag Search")
    print("-" * 50)
    
    search_terms = ["Met at", "2025-07", "deployment", "event", "rally"]
    
    for term in search_terms:
        try:
            print(f"   Searching for: '{term}'")
            
            # Try different filter approaches
            filter_attempts = [
                {'name': term},
                {'name': {'match': term}},
                {'name': {'prefix': term}},
                {'name': {'contains': term}}
            ]
            
            for filter_attempt in filter_attempts:
                try:
                    result = client.get_signup_tags(filters=filter_attempt)
                    tags = result.get('data', [])
                    
                    if tags:
                        print(f"      ✅ Found {len(tags)} tags with filter {filter_attempt}")
                        for tag in tags[:3]:  # Show first 3
                            tag_name = tag.get('attributes', {}).get('name', '')
                            print(f"         - '{tag_name}'")
                        break
                    
                except Exception as e:
                    continue  # Try next filter
                    
        except Exception as e:
            print(f"   ❌ Search for '{term}' failed: {e}")


def main():
    print("🎯 Smart Search for 'Met at...' Tags")
    print("=" * 60)
    print("(Avoiding downloading all 22k+ tags!)")
    print()
    
    client = load_client()
    
    # Try direct search first
    try_direct_tag_search(client)
    
    # Smart page-by-page search
    results = search_for_met_at_tags_smartly(client)
    
    print(f"\n" + "=" * 60)
    print("🎉 FINAL RESULTS:")
    
    if results['exact_matches']:
        print(f"✅ Found {len(results['exact_matches'])} EXACT matches!")
        print("   These are the tag IDs we can use in the complex filter:")
        for tag in results['exact_matches']:
            print(f"   - ID {tag['id']}: '{tag['name']}'")
    
    elif results['met_at_variations']:
        print(f"⚠️  Found {len(results['met_at_variations'])} 'Met at' variations")
        print("   You might want to use these instead:")
        for tag in results['met_at_variations'][:5]:
            print(f"   - ID {tag['id']}: '{tag['name']}'")
    
    elif results['july_2025_tags']:
        print(f"🔍 Found {len(results['july_2025_tags'])} July 2025 tags")
        print("   These might be related:")
        for tag in results['july_2025_tags'][:5]:
            print(f"   - ID {tag['id']}: '{tag['name']}'")
    
    else:
        print("❌ No matching tags found")
        print("   The 'Met at...' tags may not exist yet")
    
    print(f"\nSearched {results['total_searched']} out of 22k+ total tags")


if __name__ == "__main__":
    main()