# nb_path_updates/nb_nightly/filters/clickers.py
"""
Filter module for email clickers from any broadcaster (August 2025)
Finds people who clicked in emails from any broadcaster between 2025-08-01 and 2025-08-31
TESTING MODE: Only exports CSV, does NOT assign to paths
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

# from src.nb_api_client import NationBuilderClient
from nb_api_client import NationBuilderClient
from typing import Dict, List, Any, Set
import csv
from datetime import datetime, date

# Filter configuration
FILTER_NAME = "Email Clickers Filter"
FILTER_DESCRIPTION = "People who clicked emails from any broadcaster (August 2025) - TESTING MODE"

# Target path/step for assignment (NOT USED IN TESTING MODE)
TARGET_PATH_ID = "1109"  # Email Clickers path
TARGET_STEP_ID = "1386"  # Replace with the correct step ID you want to assign to

# Date range for email clicks
START_DATE = "2025-08-01"
END_DATE = "2025-08-31"


def get_email_clickers_from_broadcasts(client: NationBuilderClient, logger) -> Set[str]:
    """
    Find people who clicked emails from any broadcaster between START_DATE and END_DATE
    
    This involves:
    1. Getting email blasts (broadcasts) from the date range
    2. Getting email recipients who clicked those blasts
    """
    logger.info(f"   Finding email clickers from {START_DATE} to {END_DATE}...")
    
    all_clicker_ids = set()
    
    try:
        # Step 1: Get email blasts from the date range
        logger.debug("      Getting email blasts from date range...")
        
        # Get email blasts - we'll need to filter by date
        blast_ids = []
        page = 1
        
        while True:
            # Get blasts - the API endpoint might be /blasts or /emails
            try:
                # Try blasts endpoint first
                response = client.session.get(f"{client.base_url}/blasts", params={'page[size]': 100})
                
                if response.status_code != 200:
                    # Try different endpoint names
                    response = client.session.get(f"{client.base_url}/email_blasts", params={'page[size]': 100})
                
                if response.status_code != 200:
                    logger.error(f"      Could not access email blasts endpoint: {response.status_code}")
                    break
                
                data = response.json()
                blasts = data.get('data', [])
                
                if not blasts:
                    break
                
                # Filter blasts by date range
                for blast in blasts:
                    attrs = blast.get('attributes', {})
                    created_at = attrs.get('created_at', '')
                    
                    # Extract date from created_at (format: "2025-08-15T10:30:00-04:00")
                    if created_at:
                        try:
                            blast_date = created_at.split('T')[0]  # Get just the date part
                            if START_DATE <= blast_date <= END_DATE:
                                blast_ids.append(blast.get('id'))
                        except:
                            continue
                
                if len(blasts) < 100:
                    break
                    
                page += 1
                if page > 50:  # Safety limit
                    break
                    
            except Exception as e:
                logger.warning(f"      Error getting blasts: {e}")
                break
        
        logger.debug(f"      Found {len(blast_ids)} email blasts in date range")
        
        if not blast_ids:
            logger.warning("      No email blasts found in date range")
            return set()
        
        # Step 2: Get recipients who clicked these blasts
        logger.debug(f"      Getting clickers for {len(blast_ids)} blasts...")
        
        for i, blast_id in enumerate(blast_ids[:20]):  # Limit to first 20 blasts for efficiency
            logger.debug(f"         Checking blast {i+1}/{min(len(blast_ids), 20)}: {blast_id}")
            
            page = 1
            while True:
                try:
                    # Get email recipients for this blast
                    response = client.session.get(
                        f"{client.base_url}/email_recipients",
                        params={
                            'filter[blast_id]': blast_id,
                            'page[size]': 100
                        }
                    )
                    
                    if response.status_code != 200:
                        logger.debug(f"         Could not get recipients for blast {blast_id}: {response.status_code}")
                        break
                    
                    data = response.json()
                    recipients = data.get('data', [])
                    
                    if not recipients:
                        break
                    
                    # Look for recipients who clicked
                    for recipient in recipients:
                        attrs = recipient.get('attributes', {})
                        
                        # Check if they clicked (different possible field names)
                        clicked = (
                            attrs.get('clicked_at') or 
                            attrs.get('click_count', 0) > 0 or
                            attrs.get('clicked', False) or
                            attrs.get('status') == 'clicked'
                        )
                        
                        if clicked:
                            signup_id = attrs.get('signup_id')
                            if signup_id:
                                all_clicker_ids.add(signup_id)
                    
                    if len(recipients) < 100:
                        break
                        
                    page += 1
                    if page > 10:  # Safety limit per blast
                        break
                        
                except Exception as e:
                    logger.debug(f"         Error getting recipients for blast {blast_id}: {e}")
                    break
        
        logger.info(f"   ✅ Found {len(all_clicker_ids)} unique email clickers")
        return all_clicker_ids
        
    except Exception as e:
        logger.error(f"   ❌ Error finding email clickers: {e}")
        return set()


def get_email_clickers_alternative_approach(client: NationBuilderClient, logger) -> Set[str]:
    """
    Alternative approach: Look for email recipients directly with date and click filters
    """
    logger.info("   🔄 Trying alternative approach for email clickers...")
    
    all_clicker_ids = set()
    
    try:
        # Try to get email recipients with filters
        page = 1
        
        while True:
            try:
                # Try different filter combinations
                filter_params = {
                    'page[size]': 100,
                    # Try filtering by date range
                    'filter[created_at][gte]': START_DATE,
                    'filter[created_at][lte]': END_DATE,
                }
                
                response = client.session.get(f"{client.base_url}/email_recipients", params=filter_params)
                
                if response.status_code != 200:
                    logger.debug(f"      Email recipients filter failed: {response.status_code}")
                    break
                
                data = response.json()
                recipients = data.get('data', [])
                
                if not recipients:
                    break
                
                # Filter for clickers
                for recipient in recipients:
                    attrs = recipient.get('attributes', {})
                    
                    # Check if they clicked
                    clicked = (
                        attrs.get('clicked_at') or 
                        attrs.get('click_count', 0) > 0 or
                        attrs.get('clicked', False) or
                        attrs.get('status') == 'clicked'
                    )
                    
                    if clicked:
                        signup_id = attrs.get('signup_id')
                        if signup_id:
                            all_clicker_ids.add(signup_id)
                
                if len(recipients) < 100:
                    break
                    
                page += 1
                if page > 100:  # Safety limit
                    break
                    
            except Exception as e:
                logger.debug(f"      Error in alternative approach: {e}")
                break
        
        logger.info(f"   ✅ Alternative approach found {len(all_clicker_ids)} clickers")
        return all_clicker_ids
        
    except Exception as e:
        logger.error(f"   ❌ Alternative approach failed: {e}")
        return set()


def apply_path_exclusions_clickers(client: NationBuilderClient, signup_ids: Set[str], logger) -> Set[str]:
    """
    Apply path exclusion rules specific to clickers filter:
    - NOT on path 1110 (Top Circles)
    - NOT completed path 1109 (Email Clickers)
    - NOT abandoned path 1109
    - NOT on steps 1381, 1383, 1380 (for path 1109)
    """
    logger.info(f"   Applying clicker-specific path exclusions to {len(signup_ids)} people...")
    
    excluded_signup_ids = set()
    
    try:
        # Exclusion 1: Path 1110 (Top Circles) - anyone on this path is excluded
        logger.debug("      Checking path 1110 (Top Circles) exclusions...")
        page = 1
        while True:
            result = client.get_path_journeys(filters={'path_id': '1110'}, page_size=100)
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
            if page > 20:
                break
        
        path_1110_exclusions = len([sid for sid in excluded_signup_ids if sid in signup_ids])
        logger.debug(f"         Excluded {path_1110_exclusions} people from path 1110")
        
        # Exclusion 2: Path 1109 (Email Clickers) rules
        logger.debug("      Checking path 1109 (Email Clickers) exclusions...")
        page = 1
        path_1109_exclusions = 0
        
        while True:
            result = client.get_path_journeys(filters={'path_id': '1109'}, page_size=100)
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
                    
                    # Check if completed or abandoned path 1109
                    if status in ['completed', 'abandoned']:
                        should_exclude = True
                        
                    # Check if on exclusion steps 1381, 1383, 1380
                    elif path_step_id in ['1381', '1383', '1380']:
                        should_exclude = True
                    
                    if should_exclude:
                        excluded_signup_ids.add(signup_id)
                        path_1109_exclusions += 1
            
            if len(journeys) < 100:
                break
            page += 1
            if page > 50:  # Might be more journeys for this path
                break
        
        logger.debug(f"         Excluded {path_1109_exclusions} people from path 1109 rules")
        
        remaining = signup_ids - excluded_signup_ids
        total_excluded = len(excluded_signup_ids)
        logger.info(f"   ✅ After exclusions: {len(remaining)} people remain ({total_excluded} excluded)")
        
        return remaining
        
    except Exception as e:
        logger.error(f"   ❌ Error applying path exclusions: {e}")
        return signup_ids


def get_final_records_and_filter_banned(client: NationBuilderClient, signup_ids: Set[str], logger) -> List[Dict[str, Any]]:
    """Get full records and filter out banned people"""
    logger.info(f"   Getting final records and filtering banned people...")
    
    final_signups = []
    signup_id_list = list(signup_ids)
    
    for i, signup_id in enumerate(signup_id_list):
        if i % 50 == 0:
            logger.debug(f"      Processing {i+1}/{len(signup_id_list)}...")
        
        try:
            signup_result = client.get_signup_by_id(
                signup_id, 
                fields=['first_name', 'last_name', 'email', 'banned_at', 'id', 'created_at']
            )
            
            signup = signup_result.get('data')
            if signup:
                attrs = signup.get('attributes', {})
                if not attrs.get('banned_at'):  # Not banned
                    final_signups.append(signup)
                    
        except Exception:
            continue
    
    logger.info(f"   ✅ Final count: {len(final_signups)} people (after banned filter)")
    return final_signups


def export_results_to_csv(people: List[Dict[str, Any]], logger) -> str:
    """Export results to CSV for record-keeping"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"email_clickers_results_{timestamp}.csv"
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ID', 'First Name', 'Last Name', 'Email', 'Created At']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for person in people:
                attrs = person.get('attributes', {})
                writer.writerow({
                    'ID': person.get('id', ''),
                    'First Name': attrs.get('first_name', ''),
                    'Last Name': attrs.get('last_name', ''),
                    'Email': attrs.get('email', ''),
                    'Created At': attrs.get('created_at', '')
                })
        
        logger.info(f"   📄 Results exported to: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"   ❌ CSV export failed: {e}")
        return None


def run_filter(client: NationBuilderClient, logger) -> Dict[str, Any]:
    """
    Main function that implements the filter interface
    This is called by the main orchestrator
    
    TESTING MODE: Only exports CSV, does NOT assign to NationBuilder paths
    """
    logger.info(f"🎯 {FILTER_NAME}")
    logger.info(f"   {FILTER_DESCRIPTION}")
    logger.info(f"   Date range: {START_DATE} to {END_DATE}")
    logger.info("   ⚠️  TESTING MODE: CSV export only, NO path assignments")
    
    # Step 1: Find email clickers
    clicker_ids = get_email_clickers_from_broadcasts(client, logger)
    
    # If first approach didn't work well, try alternative
    if len(clicker_ids) < 10:  # Seems low, try alternative
        logger.info("   🔄 First approach found few results, trying alternative...")
        alt_clicker_ids = get_email_clickers_alternative_approach(client, logger)
        clicker_ids.update(alt_clicker_ids)  # Combine results
    
    if not clicker_ids:
        logger.warning("   No email clickers found in date range")
        return {
            'people_count': 0,
            'csv_filename': None
        }
    
    # Step 2: Apply path exclusions
    clickers_after_exclusions = apply_path_exclusions_clickers(client, clicker_ids, logger)
    
    if not clickers_after_exclusions:
        logger.warning("   No clickers remaining after path exclusions")
        return {
            'people_count': 0,
            'csv_filename': None
        }
    
    # Step 3: Get records and filter banned
    final_clickers = get_final_records_and_filter_banned(client, clickers_after_exclusions, logger)
    
    if not final_clickers:
        logger.warning("   No clickers remaining after banned filter")
        return {
            'people_count': 0,
            'csv_filename': None
        }
    
    # Step 4: TESTING MODE - Only export CSV, NO path assignment
    logger.info(f"   ⚠️  TESTING MODE: Skipping path assignment for {len(final_clickers)} people")
    
    # Step 5: Export results
    csv_filename = export_results_to_csv(final_clickers, logger)
    
    return {
        'people_count': len(final_clickers),
        'csv_filename': csv_filename
    }