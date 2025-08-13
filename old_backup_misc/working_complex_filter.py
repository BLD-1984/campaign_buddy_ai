# tests/working_complex_filter.py
"""
Working complex filter implementation using the ACTUAL tag format we discovered
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import csv
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from nb_api_client import NationBuilderClient
from typing import List, Dict, Any, Set


def load_client():
    return NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )


def find_met_at_tag_ids_working(client: NationBuilderClient) -> List[str]:
    """
    Find all tag IDs that match the ACTUAL format:
    'Met at deployment on 2025-07-XX', 'Met at event on 2025-07-XX', etc.
    """
    print("🏷️  Finding 'Met at...' tag IDs (ACTUAL FORMAT)")
    print("-" * 40)
    
    # Updated patterns based on what we actually found
    search_patterns = [
        "met at deployment on 2025-07",
        "met at event on 2025-07", 
        "met at rally on 2025-07",
        "met at online on 2025-07",
        "met at other on 2025-07"
    ]
    
    matching_tag_ids = []
    
    try:
        page = 1
        total_searched = 0
        
        while page <= 300:  # Search up to 30k tags
            result = client.get_signup_tags(page_size=100)
            tags = result.get('data', [])
            
            if not tags:
                break
                
            total_searched += len(tags)
            
            # Search this page for our patterns
            for tag in tags:
                tag_name = tag.get('attributes', {}).get('name', '').lower()
                tag_id = tag.get('id')
                original_name = tag.get('attributes', {}).get('name', '')
                
                # Check if this tag starts with any of our patterns
                for pattern in search_patterns:
                    if tag_name.startswith(pattern):
                        matching_tag_ids.append(tag_id)
                        print(f"   🎯 MATCH: '{original_name}' (ID: {tag_id})")
                        break
            
            # Progress update
            if page % 50 == 0:
                print(f"   📊 Page {page}: Searched {total_searched} tags, found {len(matching_tag_ids)} matches")
            
            # Stop if we found a good number or hit end
            if len(tags) < 100:
                break
            page += 1
            
            # Safety break
            if len(matching_tag_ids) > 100:
                print(f"   ✅ Found 100+ matching tags, that should be enough")
                break
        
        print(f"✅ Found {len(matching_tag_ids)} matching 'Met at...' tags")
        print(f"📊 Searched {total_searched} total tags")
        return matching_tag_ids
        
    except Exception as e:
        print(f"❌ Error finding tags: {e}")
        return []


def get_people_with_met_at_tags_working(client: NationBuilderClient, tag_ids: List[str]) -> Set[str]:
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
        print(f"🔍 Checking {len(tag_ids)} tag IDs...")
        
        for i, tag_id in enumerate(tag_ids, 1):
            print(f"   {i}/{len(tag_ids)} Checking tag ID: {tag_id}")
            
            # Get all people with this tag
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
            
            tag_count = len([t for t in taggings if t.get('attributes', {}).get('signup_id')])
            if tag_count > 0:
                print(f"      Found {tag_count} people with this tag")
    
        print(f"✅ Total unique people with Met at tags: {len(all_signup_ids)}")
        return all_signup_ids
        
    except Exception as e:
        print(f"❌ Error getting people with tags: {e}")
        return set()


def apply_path_exclusions_working(client: NationBuilderClient, signup_ids: Set[str]) -> Set[str]:
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
        print(f"   Checking path exclusions for {len(signup_ids)} people...")
        
        # Get ALL path journeys for the relevant paths
        paths_to_check = ['1110', '1111']  # Top Circles and Field Signups
        
        for path_id in paths_to_check:
            print(f"   🔍 Checking path {path_id}...")
            
            page = 1
            while True:
                result = client.get_path_journeys(
                    filters={'path_id': path_id},
                    page_size=100
                )
                
                journeys = result.get('data', [])
                if not journeys:
                    break
                
                for journey in journeys:
                    attrs = journey.get('attributes', {})
                    signup_id = attrs.get('signup_id')
                    status = attrs.get('status', '').lower() if attrs.get('status') else ''
                    path_step_id = attrs.get('path_step_id')
                    
                    if signup_id in signup_ids:
                        should_exclude = False
                        reason = ""
                        
                        if path_id == '1110':
                            # Anyone on Top Circles path is excluded
                            should_exclude = True
                            reason = "on path 1110 (Top Circles)"
                        
                        elif path_id == '1111':
                            # Check Field Signups path conditions
                            if status in ['completed', 'abandoned']:
                                should_exclude = True
                                reason = f"{status} path 1111 (Field Signups)"
                            elif path_step_id in ['1393', '1394']:
                                should_exclude = True
                                reason = f"on step {path_step_id} (Attempted/Reached)"
                        
                        if should_exclude:
                            excluded_signup_ids.add(signup_id)
                            if len(excluded_signup_ids) <= 10:  # Show first 10
                                print(f"      ❌ Excluded {signup_id}: {reason}")
                
                if len(journeys) < 100:
                    break
                page += 1
                
                if page > 20:  # Safety limit
                    break
        
        remaining_count = len(signup_ids) - len(excluded_signup_ids)
        print(f"✅ After path exclusions: {remaining_count} people remain ({len(excluded_signup_ids)} excluded)")
        
        return signup_ids - excluded_signup_ids
        
    except Exception as e:
        print(f"❌ Error applying path exclusions: {e}")
        return signup_ids


def apply_banned_filter_working(client: NationBuilderClient, signup_ids: Set[str]) -> List[Dict[str, Any]]:
    """
    Filter out banned people and return full signup records for the final list
    """
    print(f"\n🚫 Applying banned filter and getting final records")
    print("-" * 40)
    
    if not signup_ids:
        return []
    
    final_signups = []
    
    try:
        signup_id_list = list(signup_ids)
        batch_size = 50  # Larger batches for efficiency
        
        for i in range(0, len(signup_id_list), batch_size):
            batch = signup_id_list[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1}/{(len(signup_id_list)-1)//batch_size + 1}: {len(batch)} people")
            
            for signup_id in batch:
                try:
                    # Get the full signup record
                    signup_result = client.get_signup_by_id(
                        signup_id, 
                        fields=[
                            'first_name', 'last_name', 'email', 'banned_at', 'id',
                            'created_at', 'support_level', 'phone_number'
                        ]
                    )
                    
                    signup = signup_result.get('data')
                    if signup:
                        attrs = signup.get('attributes', {})
                        banned_at = attrs.get('banned_at')
                        
                        # Check if not banned
                        if not banned_at:
                            final_signups.append(signup)
                        else:
                            print(f"      ❌ Excluded {signup_id}: banned")
                            
                except Exception as e:
                    print(f"      ⚠️  Could not check signup {signup_id}: {e}")
                    continue
        
        print(f"✅ Final count after banned filter: {len(final_signups)} people")
        return final_signups
        
    except Exception as e:
        print(f"❌ Error applying banned filter: {e}")
        return []


def export_to_csv_working(people: List[Dict[str, Any]], filename: str = None) -> str:
    """Export the list of people to CSV"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"met_at_people_working_{timestamp}.csv"
    
    print(f"\n📄 Exporting to CSV: {filename}")
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'ID', 'First Name', 'Last Name', 'Email', 
                'Full Name', 'Created At', 'Support Level', 'Phone Number'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for person in people:
                attrs = person.get('attributes', {})
                
                row = {
                    'ID': person.get('id', ''),
                    'First Name': attrs.get('first_name', ''),
                    'Last Name': attrs.get('last_name', ''),
                    'Email': attrs.get('email', ''),
                    'Full Name': f"{attrs.get('first_name', '')} {attrs.get('last_name', '')}".strip(),
                    'Created At': attrs.get('created_at', ''),
                    'Support Level': attrs.get('support_level', ''),
                    'Phone Number': attrs.get('phone_number', '')
                }
                writer.writerow(row)
        
        print(f"✅ Successfully exported {len(people)} people to {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        return None


def run_working_complex_filter(client: NationBuilderClient) -> List[Dict[str, Any]]:
    """Run the complete working complex filter"""
    print("🎯 Running WORKING Complex Filter")
    print("=" * 60)
    
    # Step 1: Find the actual 'Met at...' tag IDs
    met_at_tag_ids = find_met_at_tag_ids_working(client)
    
    if not met_at_tag_ids:
        print("❌ No matching tags found. Filter cannot proceed.")
        return []
    
    # Step 2: Get people with those tags  
    people_with_tags = get_people_with_met_at_tags_working(client, met_at_tag_ids)
    
    if not people_with_tags:
        print("❌ No people found with matching tags.")
        return []
    
    # Step 3: Apply path exclusions
    people_after_path_filter = apply_path_exclusions_working(client, people_with_tags)
    
    if not people_after_path_filter:
        print("❌ No people remaining after path exclusions.")
        return []
    
    # Step 4: Apply banned filter and get final records
    final_people = apply_banned_filter_working(client, people_after_path_filter)
    
    return final_people


def main():
    """Test the working complex filter and export results"""
    print("🔍 WORKING Complex Filter Test")
    print("=" * 60)
    print("Using the ACTUAL tag format we discovered!")
    print()
    
    client = load_client()
    
    # Run the complete filter
    matching_people = run_working_complex_filter(client)
    
    print("\n" + "=" * 60)
    print("🎉 FINAL RESULTS:")
    print(f"Found {len(matching_people)} people matching all criteria")
    
    # Show sample results
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
        csv_filename = export_to_csv_working(matching_people)
        if csv_filename:
            print(f"\n📁 CSV exported successfully: {csv_filename}")
            print("🔍 Review the CSV to verify these are the correct people")
            print("📋 Next step: Choose which path step to assign them to and build the assignment function!")
        else:
            print("❌ CSV export failed")
    else:
        print("⚠️  No people found - nothing to export")
    
    return matching_people


if __name__ == "__main__":
    main()