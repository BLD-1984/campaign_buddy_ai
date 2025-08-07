# nb_path_updates/nb_nightly/utils/reporting_utils.py
"""
Utilities for generating summary reports
Updated for testing mode - no path assignments
"""

import csv
from datetime import datetime
from typing import Dict, List, Any


def generate_summary_report(results: List[Dict[str, Any]], log_filename: str) -> str:
    """Generate a summary report of all filter results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"clickers_test_summary_{timestamp}.csv"
    
    with open(report_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Filter Name', 'Success', 'People Found', 'CSV Filename', 'Error'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                'Filter Name': result['filter_name'],
                'Success': 'YES' if result['success'] else 'NO',
                'People Found': result['people_count'],
                'CSV Filename': result['csv_filename'],
                'Error': result['error'] or ''
            })
    
    return report_filename


# nb_path_updates/nb_nightly/utils/logging_utils.py
"""
Logging utilities
"""

import logging


def setup_filter_logger(filter_name: str, main_logger: logging.Logger) -> logging.Logger:
    """Create a child logger for a specific filter"""
    return main_logger.getChild(filter_name.lower().replace(' ', '_'))


# nb_path_updates/nb_nightly/utils/__init__.py
"""Utilities package"""

# from . import reporting_utils, logging_utils

__all__ = ['reporting_utils', 'logging_utils']