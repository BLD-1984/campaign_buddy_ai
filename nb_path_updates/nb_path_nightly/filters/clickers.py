# nb_path_updates/nb_nightly/filters/clickers.py
"""
Filter module for email clickers using tag ID approach
Finds people with tag ID 14890 (zi-c-24h - clickers within 24 hours)
Enhanced with reactivate logic and detailed debugging
"""

import sys
import os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

# from nb_api_client import NationBuilderClient, NationBuilderAPIError
from src.nb_api_client import NationBuilderClient, NationBuilderAPIError
from typing import Dict, List, Any
import csv
from datetime import datetime

# Filter configuration
FILTER_NAME = "Email Clickers Filter"
FILTER_DESCRIPTION = "People with tag ID 14890 (zi-c-24h - email clickers within 24h)"

# Target tag ID to find
TARGET_TAG_ID = "14890"
TARGET_TAG_NAME = "zi-c-24h"

# Path configuration
PATH_ID = "1109"
PATH_STEP_ID = "1380"


def find_signup_ids_with_tag_id(client: NationBuilderClient, tag_id: str, logger) -> List[str]:
    """Find all signup IDs who have the specified tag ID"""
    logger.info(f"     Finding signup IDs with tag ID: {tag_id} ({TARGET_TAG_NAME})")
    
    try:
        signup_ids = []
        page = 1
        total_processed = 0
        
        while True:
            taggings_result = client.get_signup_taggings(
                filters={'tag_id': tag_id}, 
                page_size=100
            )
            taggings = taggings_result.get('data', [])
            
            if not taggings:
                break
            
            page_signup_ids = []
            for tagging in taggings:
                tagging_attrs = tagging.get('attributes', {})
                signup_id = tagging_attrs.get('signup_id')
                if signup_id:
                    page_signup_ids.append(str(signup_id))
            
            signup_ids.extend(page_signup_ids)
            total_processed += len(taggings)
            
            logger.debug(f"         Page {page}: Found {len(page_signup_ids)} signup IDs, total so far: {len(signup_ids)}")
            
            if len(taggings) < 100:
                break
                
            page += 1
            
            if page > 1000:  # Safety limit
                logger.warning(f"      Reached safety limit of 1000 pages")
                break
        
        unique_signup_ids = list(set(signup_ids))
        logger.info(f"    Found {len(unique_signup_ids)} unique signup IDs with tag ID {tag_id}")
        
        return unique_signup_ids
        
    except Exception as e:
        logger.error(f"    Error finding signup IDs with tag ID {tag_id}: {e}")
        return []


def export_signup_ids_to_csv(signup_ids: List[str], tag_id: str, logger) -> str:
    """Export signup IDs to CSV for record-keeping"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{date_str}_clickers_update_tag_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Signup_ID', 'Tag_ID', 'Tag_Name', 'Export_Timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for signup_id in signup_ids:
                writer.writerow({
                    'Signup_ID': signup_id,
                    'Tag_ID': tag_id,
                    'Tag_Name': TARGET_TAG_NAME,
                    'Export_Timestamp': timestamp
                })
        logger.info(f"    Signup IDs exported to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"    CSV export failed: {e}")
        return None


def process_signup_path_journey(client: NationBuilderClient, signup_id: str, logger) -> bool:
    """
    Enhanced logic: 
    1. Check if signup has ANY journey on path 1109 (active or inactive)
    2. If active journey → update to step 1380
    3. If inactive journey → reactivate at step 1380
    4. If no journey → create new journey at step 1380
    
    Returns True if successful, False if failed
    """
    # DEBUG: Check what values we're working with
    logger.info(f" PATH_STEP_ID value: '{PATH_STEP_ID}' (type: {type(PATH_STEP_ID)})")
    
    try:
        # First, let's see ALL path journeys for this signup to understand what's happening
        logger.info(f"       Checking all path journeys for signup {signup_id}")
        all_journeys_url = f"{client.base_url}/path_journeys"
        all_journeys_params = {'filter[signup_id]': signup_id}
        all_response = client._make_request('GET', all_journeys_url, params=all_journeys_params)
        all_data = client._handle_response(all_response)
        
        all_journeys = all_data.get('data', [])
        logger.info(f"       Found {len(all_journeys)} total path journeys for signup {signup_id}")
        
        target_journey = None
        for journey in all_journeys:
            journey_id = journey['id']
            attrs = journey['attributes']
            path_id = attrs.get('path_id')
            current_step = attrs.get('current_step_id')
            status = attrs.get('journey_status')
            logger.info(f"         - Journey {journey_id}: path {path_id}, step {current_step}, status {status}")
            
            # Look for ANY journey on our target path (active or inactive)
            if path_id == PATH_ID:
                target_journey = journey
        
        if target_journey:
            # They have a journey on path 1109 (might be active or inactive)
            journey_id = target_journey['id']
            current_step = target_journey['attributes'].get('current_step_id')
            current_status = target_journey['attributes'].get('journey_status')
            
            logger.info(f"       Signup {signup_id} HAS a journey on path {PATH_ID}")
            logger.info(f"         Journey ID: {journey_id}")
            logger.info(f"         Current step: {current_step}")
            logger.info(f"         Current status: {current_status}")
            
            if current_step == PATH_STEP_ID and current_status == 'active':
                logger.info(f"       Signup {signup_id} already on correct step {PATH_STEP_ID} and active")
                return True
            elif current_status == 'active':
                # Active journey, just update the step
                logger.info(f"       Updating active journey {journey_id} from step {current_step} to step {PATH_STEP_ID}")
                step_id_to_send = str(PATH_STEP_ID)
                logger.info(f"       About to call update_path_journey_step with step_id='{step_id_to_send}'")
                
                update_result = client.update_path_journey_step(journey_id, step_id_to_send)
                logger.info(f"       Update result: {update_result}")
                logger.info(f"       Journey updated successfully")
                return True
            else:
                # Inactive journey, reactivate it at the new step
                logger.info(f"       Reactivating inactive journey {journey_id} at step {PATH_STEP_ID}")
                step_id_to_send = str(PATH_STEP_ID)
                logger.info(f"       About to call reactivate_path_journey with step_id='{step_id_to_send}'")
                
                reactivate_result = client.reactivate_path_journey(journey_id, step_id_to_send)
                logger.info(f"       Reactivate result: {reactivate_result}")
                logger.info(f"       Journey reactivated successfully")
                return True
        else:
            # They have no journey on path 1109, create new journey
            logger.info(f"       Signup {signup_id} has NO journey on path {PATH_ID} - creating new journey")
            step_id_to_send = str(PATH_STEP_ID)
            logger.info(f"       About to call create_path_journey with step_id='{step_id_to_send}'")
            
            create_result = client.create_path_journey(signup_id, PATH_ID, step_id_to_send)
            logger.info(f"       Create result: {create_result}")
            logger.info(f"       New journey created successfully")
            return True
            
    except NationBuilderAPIError as e:
        logger.error(f"       API error for signup {signup_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"       Unexpected error for signup {signup_id}: {e}")
        return False


def run_filter(client: NationBuilderClient, logger) -> Dict[str, Any]:
    """Main function that implements the filter interface"""
    logger.info(f" {FILTER_NAME}")
    logger.info(f"   {FILTER_DESCRIPTION}")
    logger.info(f"   Target tag ID: {TARGET_TAG_ID} ({TARGET_TAG_NAME})")
    logger.info(f"   Target path: {PATH_ID}, step: {PATH_STEP_ID}")
    logger.info("    Enhanced logic: Update, reactivate, or create journeys")

    # Find signup IDs with the target tag ID
    signup_ids = find_signup_ids_with_tag_id(client, TARGET_TAG_ID, logger)

    if not signup_ids:
        logger.warning(f"   No signup IDs found with tag ID {TARGET_TAG_ID}")
        return {
            'people_count': 0,
            'csv_filename': None,
            'list_slug': None,
            'list_id': None
        }

    # Export signup IDs to CSV
    csv_filename = export_signup_ids_to_csv(signup_ids, TARGET_TAG_ID, logger)

    # Create a unique list and add people
    date_str = datetime.now().strftime("%y%m%d")
    base_slug = f"_{date_str}i_c_"
    suffix = 1
    while True:
        list_slug = f"{base_slug}{suffix}"
        existing_list = client.list_exists(list_slug)
        if not existing_list:
            break
        suffix += 1

    logger.info(f"    Creating new list with slug: {list_slug}")
    admin_signup_id = os.getenv("NB_ADMIN_SIGNUP_ID")
    if not admin_signup_id:
        logger.error(" NB_ADMIN_SIGNUP_ID not set in environment. Cannot create list.")
        return {
            'people_count': len(signup_ids),
            'csv_filename': csv_filename,
            'list_slug': list_slug,
            'list_id': None
        }

    try:
        list_obj = client.create_list(list_slug, list_slug, admin_signup_id)
        list_id = list_obj['data']['id']
        logger.info(f"    List created successfully with ID: {list_id}")

        # Add people to the list
        logger.info(f"    Adding {len(signup_ids)} people to list {list_slug}")
        add_result = client.add_people_to_list(list_id, signup_ids)
        logger.info(f"    People added to list")

    except Exception as e:
        logger.error(f"    Error creating/populating list: {e}")
        list_id = None

    # Process path journeys with enhanced logic
    logger.info(f"     Processing path journeys for {len(signup_ids)} people...")
    
    successful_updates = 0
    errors = 0

    for i, signup_id in enumerate(signup_ids):
        if i % 10 == 0:  # Progress logging every 10 people
            logger.info(f"      Progress: {i+1}/{len(signup_ids)} processed")
        
        logger.debug(f"   Processing signup {i+1}/{len(signup_ids)}: {signup_id}")
        
        success = process_signup_path_journey(client, signup_id, logger)
        
        if success:
            successful_updates += 1
        else:
            errors += 1

    # Summary
    logger.info(f"    Path Journey Results:")
    logger.info(f"       Successful: {successful_updates}")
    logger.info(f"       Errors: {errors}")

    logger.info(f"    COMPLETE: Created list '{list_slug}', added {len(signup_ids)} people, processed path journeys")

    return {
        'people_count': len(signup_ids),
        'csv_filename': csv_filename,
        'list_slug': list_slug,
        'list_id': list_id,
        'path_updates_successful': successful_updates,
        'path_updates_errors': errors
    }