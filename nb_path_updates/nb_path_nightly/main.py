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

# from src.nb_api_client import NationBuilderClient
from nb_api_client import NationBuilderClient

# Import ONLY the clickers filter for testing
from filters import clickers

# Import utilities
from utils import logging_utils, reporting_utils


def setup_logging():
    """Setup logging for the nightly run"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"clickers_test_run_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    return logging.getLogger(__name__), log_filename


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
    logger.info(f"🎯 Starting filter: {filter_name}")
    
    try:
        # Each filter module implements this interface
        result = filter_module.run_filter(client, logger)
        
        logger.info(f"✅ {filter_name} completed successfully")
        logger.info(f"   Found: {result.get('people_count', 0)} people")
        logger.info(f"   CSV exported: {result.get('csv_filename', 'None')}")
        
        return {
            'filter_name': filter_name,
            'success': True,
            'people_count': result.get('people_count', 0),
            'csv_filename': result.get('csv_filename'),
            'error': None
        }
        
    except Exception as e:
        logger.error(f"❌ {filter_name} failed: {str(e)}")
        return {
            'filter_name': filter_name,
            'success': False,
            'people_count': 0,
            'csv_filename': None,
            'error': str(e)
        }


def main():
    """Main orchestrator function - CLICKERS ONLY for testing"""
    # Setup
    logger, log_filename = setup_logging()
    logger.info("🚀 Starting Clickers Filter Test Run")
    logger.info("=" * 60)
    
    # Initialize client
    try:
        client = load_client()
        logger.info("✅ NationBuilder client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize client: {e}")
        return
    
    # Run ONLY the clickers filter
    logger.info("📋 Running CLICKERS filter only (testing mode)")
    
    result = run_filter_module(clickers, client, logger)
    
    # Generate summary report
    logger.info("\n" + "=" * 60)
    logger.info("📊 CLICKERS TEST RUN SUMMARY")
    logger.info("=" * 60)
    
    if result['success']:
        logger.info(f"✅ {result['filter_name']}: {result['people_count']} people found")
        logger.info(f"📄 CSV exported: {result['csv_filename']}")
    else:
        logger.info(f"❌ {result['filter_name']}: FAILED - {result['error']}")
    
    # Generate and save summary report
    try:
        report_filename = reporting_utils.generate_summary_report([result], log_filename)
        logger.info(f"📄 Summary report saved: {report_filename}")
    except Exception as e:
        logger.error(f"⚠️  Could not generate summary report: {e}")
    
    # Log completion
    if result['success']:
        logger.info("🎉 Clickers filter test completed successfully!")
    else:
        logger.warning("⚠️  Clickers filter test failed - check logs for details")
    
    logger.info("✅ Test run completed")
    
    return [result]


if __name__ == "__main__":
    main()