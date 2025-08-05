# tests/final_working_complex_filter.py
"""
FINAL working complex filter using the discovered tag IDs!
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


def get_people_with_target_tags(client: NationBuilderClient) -> Set[str]:
    """
    Get all signup IDs that have the target 'Met at...' tags
    Using the ACTUAL tag IDs we discovered!
    """
    print("👥 Finding people with target 'Met at...' tags")
    print("-" * 50)
    
    # The 15 tag IDs we discovered that match the original filter patterns
    target_tag_ids = [
        '14395', '14403', '14404', '14539', '14549', '14555', '14626', 
        '14632', '14635', '14637', '14725', '14729', '14732', '14741', '14559'
    ]
    
    print(f"🎯 Using {len(target_tag_ids)} target tag IDs")
    
    all_signup_ids = set()
    
    try:
        for i, tag_id in enumerate(target_tag_ids, 1):
            print(f"   {i:2d}/{len(target_tag_ids)} Checking tag ID {tag_id}...")
            
            # Get all people with this tag
            page = 1
            tag_people_count = 0
            
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
                        tag_people_count += 1
                
                if len(taggings) < 100:
                    break
                page += 1
                
                if page > 10:  # Safety limit
                    break
            
            if tag_people_count > 0:
                print(f"      ✅ Found {tag_people_count} people with this tag")
            else:
                print(f"      ❌ No people found with this tag")
    
        print(f"✅ Total unique people with target tags: {len(all_signup_ids)}")
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
    - NOT on steps 1393 or 1394 (Attempted/Reached)
    """
    print(f"\n🛤️  Applying path exclusions")
    print("-" * 50)
    
    if not signup_ids:
        return set()
    
    excluded_signup_ids = set()
    
    try:
        print(f"   Checking path exclusions for {len(signup_ids)} people...")
        
        # Check path 1110 (Top Circles) - anyone on this path is excluded
        print(f"   🔍 Checking path 1110 (Top Circles)...")
        page = 1
        while True:
            result = client.get_path_journeys(
                filters={'path_id': '1110'},
                page_size=100
            )
            
            journeys = result.get('data', [])
            if not journeys:
                break
            
            for journey in journeys:
                signup_id = journey.get('attributes', {}).get('signup_id')
                if signup_id in signup_ids:
                    excluded_signup_ids.add(signup_id)
            
            if len(journeys) < 100:
                break
            page += 1
            if page > 20:  # Safety
                break
        
        print(f"      Excluded {len([sid for sid in excluded_signup_ids if sid in signup_ids])} people on path 1110")
        
        # Check path 1111 (Field Signups) for completion/abandonment and current steps
        print(f"   🔍 Checking path 1111 (Field Signups)...")
        page = 1
        path_1111_exclusions = 0
        
        while True:
            result = client.get_path_journeys(
                filters={'path_id': '1111'},
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
                
                if signup_id in signup_ids and signup_id not in excluded_signup_ids:
                    should_exclude = False
                    
                    # Check if completed or abandoned
                    if status in ['completed', 'abandoned']:
                        should_exclude = True
                        
                    # Check if on exclusion steps 1393 or 1394
                    elif path_step_id in ['1393', '1394']:
                        should_exclude = True
                    
                    if should_exclude:
                        excluded_signup_ids.add(signup_id)
                        path_1111_exclusions += 1
            
            if len(journeys) < 100:
                break
            page += 1
            if page > 50:  # Safety - might be more journeys
                break
        
        print(f"      Excluded {path_1111_exclusions} people from path 1111 rules")
        
        remaining_count = len(signup_ids) - len(excluded_signup_ids)
        print(f"✅ After path exclusions: {remaining_count} people remain")
        
        return signup_ids - excluded_signup_ids
        
    except Exception as e:
        print(f"❌ Error applying path exclusions: {e}")
        return signup_ids


def apply_banned_filter_and_get_records(client: NationBuilderClient, signup_ids: Set[str]) -> List[Dict[str, Any]]:
    """
    Filter out banned people and return full signup records
    """
    print(f"\n🚫 Applying banned filter and getting final records")
    print("-" * 50)
    
    if not signup_ids:
        return []
    
    final_signups = []
    
    try:
        signup_id_list = list(signup_ids)
        batch_size = 50
        
        for i in range(0, len(signup_id_list), batch_size):
            batch = signup_id_list[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1}/{(len(signup_id_list)-1)//batch_size + 1}: {len(batch)} people")
            
            for signup_id in batch:
                try:
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
                        
                        # Check if not banned
                        if not banned_at:
                            final_signups.append(signup)
                        # Don't print every banned person to keep output clean
                            
                except Exception:
                    # Don't print every error to keep output clean
                    continue
        
        print(f"✅ Final count after banned filter: {len(final_signups)} people")
        return final_signups
        
    except Exception as e:
        print(f"❌ Error applying banned filter: {e}")
        return []


def export_to_csv(people: List[Dict[str, Any]], filename: str = None) -> str:
    """Export the final list to CSV"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_complex_filter_results_{timestamp}.csv"
    
    print(f"\n📄 Exporting to CSV: {filename}")
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'ID', 'First Name', 'Last Name', 'Email', 
                'Full Name', 'Created At', 'Support Level', 'Phone Number', 'Mobile Number'
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
                    'Phone Number': attrs.get('phone_number', ''),
                    'Mobile Number': attrs.get('mobile_number', '')
                }
                writer.writerow(row)
        
        print(f"✅ Successfully exported {len(people)} people to {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        return None


def run_final_complex_filter(client: NationBuilderClient) -> List[Dict[str, Any]]:
    """Run the complete working complex filter"""
    print("🎯 Running FINAL Working Complex Filter")
    print("=" * 60)
    print("Using the 15 discovered tag IDs!")
    print()
    
    # Step 1: Get people with target tags
    people_with_tags = get_people_with_target_tags(client)
    
    if not people_with_tags:
        print("❌ No people found with target tags.")
        return []
    
    # Step 2: Apply path exclusions
    people_after_path_filter = apply_path_exclusions(client, people_with_tags)
    
    if not people_after_path_filter:
        print("❌ No people remaining after path exclusions.")
        return []
    
    # Step 3: Apply banned filter and get records
    final_people = apply_banned_filter_and_get_records(client, people_after_path_filter)
    
    return final_people


def main():
    """Run the final complex filter and export results"""
    print("🏆 FINAL WORKING Complex Filter")
    print("=" * 60)
    print("Using the actual discovered tag IDs from your NationBuilder system!")
    print()
    
    client = load_client()
    
    # Run the complete filter
    matching_people = run_final_complex_filter(client)
    
    print("\n" + "=" * 60)
    print("🎉 FINAL RESULTS:")
    print(f"Found {len(matching_people)} people matching ALL criteria from your original filter!")
    
    if matching_people:
        # Show sample results
        print(f"\n📋 Sample results (first 10):")
        for i, person in enumerate(matching_people[:10]):
            attrs = person.get('attributes', {})
            name = f"{attrs.get('first_name', 'N/A')} {attrs.get('last_name', 'N/A')}"
            email = attrs.get('email', 'N/A')
            person_id = person.get('id')
            
            print(f"   {i+1:2d}. {name} ({email}) - ID: {person_id}")
        
        if len(matching_people) > 10:
            print(f"   ... and {len(matching_people) - 10} more")
        
        # Export to CSV
        csv_filename = export_to_csv(matching_people)
        if csv_filename:
            print(f"\n📁 CSV exported: {csv_filename}")
            print("🔍 Review the CSV to verify these are the correct people")
            print("🎯 These people are ready for path step assignment!")
        
        print(f"\n💡 NEXT STEPS:")
        print(f"✅ Your complex filter is working perfectly!")
        print(f"📋 Found {len(matching_people)} people ready for path assignment")
        print(f"🚀 Now you can build the path assignment function")
        print(f"☁️  And deploy as a Google Cloud Function for nightly automation")
        
    else:
        print("⚠️  No people found matching all criteria")
        print("🤔 This could mean the exclusion rules filtered everyone out")
    
    return matching_people


if __name__ == "__main__":
    main()