# nb_path_updates/nb_nightly/main.py
"""
Main orchestrator for nightly path updates
Updated to run ONLY the clickers filter module for testing
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from dotenv import load_dotenv
load_dotenv()

from nb_api_client import NationBuilderClient

# Import ONLY the clickers filter for testing
from filters import clickers

# Import utilities
from utils import logging_utils, reporting_utils


def setup_logging():
    """Setup logging for the nightly run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    
    # Ensure outputs directory exists
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    log_filename = f"{date_str}_clickers_log_{timestamp}.log"
    log_filepath = os.path.join(output_dir, log_filename)

    # Clear any existing handlers to avoid conflicts
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    return logger, log_filepath


def load_client():
    """Initialize NationBuilder client"""
    return NationBuilderClient(
        nation_slug=os.getenv('NB_NATION_SLUG'),
        access_token=os.getenv('NB_PA_TOKEN'),
        refresh_token=os.getenv('NB_PA_TOKEN_REFRESH'),
        client_id=os.getenv('NB_PA_ID'),
        client_secret=os.getenv('NB_PA_SECRET')
    )


def run_filter_module(filter_module, client: NationBuilderClient, logger) -> Dict[str, Any]:
    """
    Run a single filter module and return results
    """
    filter_name = filter_module.FILTER_NAME
    logger.info(f" Starting filter: {filter_name}")
    
    try:
        # Each filter module implements this interface
        result = filter_module.run_filter(client, logger)
        
        logger.info(f" {filter_name} completed successfully")
        logger.info(f"   Found: {result.get('people_count', 0)} people")
        logger.info(f"   CSV exported: {result.get('csv_filename', 'None')}")
        
        # Add path journey summary if available
        if 'path_updates_successful' in result:
            logger.info(f"   Path updates successful: {result.get('path_updates_successful', 0)}")
            logger.info(f"   Path updates errors: {result.get('path_updates_errors', 0)}")
        
        return {
            'filter_name': filter_name,
            'success': True,
            'people_count': result.get('people_count', 0),
            'csv_filename': result.get('csv_filename'),
            'list_slug': result.get('list_slug'),
            'path_updates_successful': result.get('path_updates_successful', 0),
            'path_updates_errors': result.get('path_updates_errors', 0),
            'error': None
        }
        
    except Exception as e:
        logger.error(f" {filter_name} failed: {str(e)}")
        return {
            'filter_name': filter_name,
            'success': False,
            'people_count': 0,
            'csv_filename': None,
            'list_slug': None,
            'path_updates_successful': 0,
            'path_updates_errors': 0,
            'error': str(e)
        }


def main():
    """Main orchestrator function - CLICKERS with simple path logic"""
    # Setup
    logger, log_filename = setup_logging()
    logger.info(" Starting Clickers Filter Run")
    logger.info("=" * 60)
    
    # Initialize client
    try:
        client = load_client()
        logger.info(" NationBuilder client initialized")
        
        # Test connection
        if not client.test_connection():
            logger.error(" Failed to connect to NationBuilder API")
            return
            
    except Exception as e:
        logger.error(f" Failed to initialize client: {e}")
        return
    
    # Run the clickers filter
    logger.info(" Running CLICKERS filter with simple path logic")
    
    result = run_filter_module(clickers, client, logger)
    
    # Generate summary report
    logger.info("\n" + "=" * 60)
    logger.info(" CLICKERS RUN SUMMARY")
    logger.info("=" * 60)
    
    if result['success']:
        logger.info(f" {result['filter_name']}: {result['people_count']} people found")
        logger.info(f" CSV exported: {result['csv_filename']}")
        logger.info(f" List created: {result['list_slug']}")
        logger.info(f"  Path updates - Success: {result['path_updates_successful']}, "
                   f"Errors: {result['path_updates_errors']}")
    else:
        logger.info(f" {result['filter_name']}: FAILED - {result['error']}")
    
    # Generate and save summary report
    try:
        report_filename = reporting_utils.generate_summary_report([result], log_filename)
        logger.info(f" Summary report saved: {report_filename}")
    except Exception as e:
        logger.error(f"  Could not generate summary report: {e}")
    
    # Log completion
    if result['success']:
        logger.info(" Clickers filter run completed successfully!")
    else:
        logger.warning("  Clickers filter run had issues - check logs for details")
    
    logger.info(" Run completed")
    
    return [result]


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f" Fatal error in main: {e}")
        import traceback
        traceback.print_exc()