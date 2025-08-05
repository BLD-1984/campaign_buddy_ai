# complex_filter.py
"""
Implementation of the complex filter criteria:
((single_tag startswith Met at deployment on 2025-07) OR ... ) AND 
((path_id ne 1110) AND (completed ne path_1111) AND (abandoned ne path_1111) AND 
(on_step ne 1393) AND (on_step ne 1394)) AND (banned eq false)
"""

import sys
from dotenv import load_dotenv
load_dotenv()

sys.path.append('src')
from nb_api_client import NationBuilderClient
import os
from typing import List, Dict, Any, Set


def load_client():
    return NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )


def find_met_at_tag_ids(client: NationBuilderClient) -> List[str]:
    """
    Find all tag IDs that start with 'Met at...' patterns from the filter
    """
    print("🏷️  Finding 'Met at...' tag IDs")
    print("-" * 40)
    
    # The tag patterns from your filter
    tag_patterns = [
        "Met at deployment on 2025-07",
        "Met at event on 2025-07", 
        "Met at rally on 2025-07",
        "Met at online on 2025-07",
        "Met at other on 2025-07"
    ]
    
    matching_tag_ids = []
    
    try:
        # Get all signup tags (may need pagination for large numbers)
        page = 1
        all_tags = []
        
        while True:
            result = client.get_signup_tags(page_size=100)
            tags = result.get('data', [])
            
            if not tags:
                break
                
            all_tags.extend(tags)
            
            # Check if we need more pages
            if len(tags) < 100:
                break
            page += 1
            
            if page > 10:  # Safety limit
                break
        
        print(f"✅ Found {len(all_tags)} total tags")
        
        # Find matching tags
        for tag in all_tags:
            tag_name = tag.get('attributes', {}).get('name', '')
            tag_id = tag.get('id')
            
            # Check if this tag starts with any of our patterns
            for pattern in tag_patterns:
                if tag_name.startswith(pattern):
                    matching_tag_ids.append(tag_id)
                    print(f"   🎯 MATCH: '{tag_name}' (ID: {tag_id})")
                    break
        
        print(f"✅ Found {len(matching_tag_ids)} matching 'Met at...' tags")
        return matching_tag_ids
        
    except Exception as e:
        print(f"❌ Error finding Met at tags: {e}")
        return []


def get_people_with_met_at_tags(client: NationBuilderClient, tag_ids: List[str]) -> Set[str]:
    """
    Get all signup IDs that have any of the 'Met at...' tags
    """
    print(f"\n👥 Finding people with Met at tags")
    print("-" * 40)
    
    if not tag_ids:
        print("❌ No tag IDs provided")
        return set()
    
    all_signup_ids = set()
    
    try:
        # Get signup_taggings for each tag ID
        for tag_id in tag_ids:
            print(f"   Checking tag ID: {tag_id}")
            
            page = 1
            while True:
                result = client.get_signup_taggings(
                    filters={'tag_id': tag_id},
                    page_size=100
                )
                
                taggings = result.get('data', [])
                if not taggings:
                    break
                
                # Extract signup IDs
                for tagging in taggings:
                    signup_id = tagging.get('attributes', {}).get('signup_id')
                    if signup_id:
                        all_signup_ids.add(signup_id)
                
                if len(taggings) < 100:
                    break
                page += 1
                
                if page > 10:  # Safety limit
                    break
            
            print(f"      Found {len([t for t in taggings if t.get('attributes', {}).get('signup_id')])} people with this tag")
    
        print(f"✅ Total unique people with Met at tags: {len(all_signup_ids)}")
        return all_signup_ids
        
    except Exception as e:
        print(f"❌ Error getting people with tags: {e}")
        return set()


def apply_path_exclusions(client: NationBuilderClient, signup_ids: Set[str]) -> Set[str]:
    """
    Apply path-based exclusions:
    - NOT on path 1110 (Top Circles)  
    - NOT completed path 1111 (Field Signups)
    - NOT abandoned path 1111
    - NOT on steps 1393 or 1394
    """
    print(f"\n🛤️  Applying path exclusions")
    print("-" * 40)
    
    if not signup_ids:
        return set()
    
    excluded_signup_ids = set()
    
    try:
        # Get path journeys for all our candidate signups
        # We'll need to check this in batches since we can't filter by multiple signup_ids directly
        
        print(f"   Checking path exclusions for {len(signup_ids)} people...")
        
        # Check for people on path 1110 (Top Circles)
        print("   🔍 Checking path 1110 (Top Circles) exclusions...")
        path_1110_result = client.get_path_journeys(filters={'path_id': '1110'})
        path_1110_journeys = path_1110_result.get('data', [])
        
        for journey in path_1110_journeys:
            signup_id = journey.get('attributes', {}).get('signup_id')
            if signup_id in signup_ids:
                excluded_signup_ids.add(signup_id)
                print(f"      ❌ Excluded {signup_id}: on path 1110")
        
        # Check for people who completed/abandoned path 1111
        print("   🔍 Checking path 1111 (Field Signups) exclusions...")
        path_1111_result = client.get_path_journeys(filters={'path_id': '1111'})
        path_1111_journeys = path_1111_result.get('data', [])
        
        for journey in path_1111_journeys:
            attrs = journey.get('attributes', {})
            signup_id = attrs.get('signup_id')
            status = attrs.get('status', '').lower()
            path_step_id = attrs.get('path_step_id')
            
            if signup_id in signup_ids:
                # Check if completed or abandoned
                if status in ['completed', 'abandoned']:
                    excluded_signup_ids.add(signup_id)
                    print(f"      ❌ Excluded {signup_id}: {status} path 1111")
                
                # Check if on exclusion steps 1393 or 1394
                elif path_step_id in ['1393', '1394']:
                    excluded_signup_ids.add(signup_id)
                    print(f"      ❌ Excluded {signup_id}: on step {path_step_id}")
        
        remaining_count = len(signup_ids) - len(excluded_signup_ids)
        print(f"✅ After path exclusions: {remaining_count} people remain")
        
        return signup_ids - excluded_signup_ids
        
    except Exception as e:
        print(f"❌ Error applying path exclusions: {e}")
        return signup_ids


def export_to_csv(people: List[Dict[str, Any]], filename: str = None) -> str:
    """
    Export the list of people to a CSV file
    """
    import csv
    from datetime import datetime
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"met_at_people_{timestamp}.csv"
    
    print(f"\n📄 Exporting to CSV: {filename}")
    print("-" * 40)
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'ID', 'First Name', 'Last Name', 'Email', 
                'Full Name', 'Created At', 'Support Level'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data
            for person in people:
                attrs = person.get('attributes', {})
                
                row = {
                    'ID': person.get('id', ''),
                    'First Name': attrs.get('first_name', ''),
                    'Last Name': attrs.get('last_name', ''),
                    'Email': attrs.get('email', ''),
                    'Full Name': f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip(),
                    'Created At': attrs.get('created_at', ''),
                    'Support Level': attrs.get('support_level', '')
                }
                writer.writerow(row)
        
        print(f"✅ Successfully exported {len(people)} people to {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        return None


def apply_banned_filter(client: NationBuilderClient, signup_ids: Set[str]) -> List[Dict[str, Any]]:
    """
    Filter out banned people and return full signup records for the final list
    """
    print(f"\n🚫 Applying banned filter and getting final records")
    print("-" * 40)
    
    if not signup_ids:
        return []
    
    final_signups = []
    
    try:
        # We need to check each signup individually since we can't filter by multiple IDs
        # For efficiency, let's get them in batches
        signup_id_list = list(signup_ids)
        batch_size = 20
        
        for i in range(0, len(signup_id_list), batch_size):
            batch = signup_id_list[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1}: {len(batch)} people")
            
            for signup_id in batch:
                try:
                    # Get the full signup record with more fields for the CSV
                    signup_result = client.get_signup_by_id(
                        signup_id, 
                        fields=[
                            'first_name', 'last_name', 'email', 'banned_at', 'id',
                            'created_at', 'support_level', 'phone_number', 'mobile_number'
                        ]
                    )
                    
                    signup = signup_result.get('data')
                    if signup:
                        attrs = signup.get('attributes', {})
                        banned_at = attrs.get('banned_at')
                        
                        # Check if not banned (banned_at should be null/None for non-banned users)
                        if not banned_at:
                            final_signups.append(signup)
                        else:
                            print(f"      ❌ Excluded {signup_id}: banned at {banned_at}")
                            
                except Exception as e:
                    print(f"      ⚠️  Could not check signup {signup_id}: {e}")
                    continue
        
        print(f"✅ Final count after banned filter: {len(final_signups)} people")
        return final_signups
        
    except Exception as e:
        print(f"❌ Error applying banned filter: {e}")
        return []


def run_complex_filter(client: NationBuilderClient) -> List[Dict[str, Any]]:
    """
    Run the complete complex filter and return matching signups
    """
    print("🎯 Running Complex Filter")
    print("=" * 60)
    
    # Step 1: Find 'Met at...' tag IDs
    met_at_tag_ids = find_met_at_tag_ids(client)
    
    if not met_at_tag_ids:
        print("❌ No 'Met at...' tags found. Cannot proceed.")
        return []
    
    # Step 2: Get people with those tags  
    people_with_tags = get_people_with_met_at_tags(client, met_at_tag_ids)
    
    if not people_with_tags:
        print("❌ No people found with 'Met at...' tags.")
        return []
    
    # Step 3: Apply path exclusions
    people_after_path_filter = apply_path_exclusions(client, people_with_tags)
    
    if not people_after_path_filter:
        print("❌ No people remaining after path exclusions.")
        return []
    
    # Step 4: Apply banned filter and get final records
    final_people = apply_banned_filter(client, people_after_path_filter)
    
    return final_people


def main():
    """Test the complex filter and export results to CSV"""
    print("🔍 Complex Filter Test")
    print("=" * 60)
    
    client = load_client()
    
    # Run the complete filter
    matching_people = run_complex_filter(client)
    
    print("\n" + "=" * 60)
    print("🎉 FINAL RESULTS:")
    print(f"Found {len(matching_people)} people matching all criteria")
    
    # Show sample results (first 10)
    for i, person in enumerate(matching_people[:10]):
        attrs = person.get('attributes', {})
        name = f"{attrs.get('first_name', 'N/A')} {attrs.get('last_name', 'N/A')}"
        email = attrs.get('email', 'N/A')
        person_id = person.get('id')
        
        print(f"   {i+1}. {name} ({email}) - ID: {person_id}")
    
    if len(matching_people) > 10:
        print(f"   ... and {len(matching_people) - 10} more")
    
    # Export to CSV
    if matching_people:
        csv_filename = export_to_csv(matching_people)
        if csv_filename:
            print(f"\n📁 CSV exported successfully: {csv_filename}")
            print("🔍 Review the CSV to verify these are the correct people")
            print("📋 Next step: Decide which path step to assign them to")
        else:
            print("❌ CSV export failed")
    else:
        print("⚠️  No people found - nothing to export")
    
    return matching_people


if __name__ == "__main__":
    main()