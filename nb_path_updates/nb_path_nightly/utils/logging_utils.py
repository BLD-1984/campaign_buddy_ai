# nb_path_updates/nb_nightly/utils/logging_utils.py
"""
Comprehensive logging utilities for NationBuilder filter operations
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional


class FilterFormatter(logging.Formatter):
    """Custom formatter with color coding for different log levels"""
    
    # Color codes for console output
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color for console output
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)


def setup_main_logger(log_level: str = "INFO") -> tuple[logging.Logger, str]:
    """
    Set up the main logger for the nightly run
    Returns: (logger, log_filename)
    """
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(logs_dir, f"nightly_run_{timestamp}.log")
    
    # Create logger
    logger = logging.getLogger("nightly_runner")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # File handler - detailed logging
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - cleaner output with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = FilterFormatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_filename


def setup_filter_logger(filter_name: str, main_logger: logging.Logger) -> logging.Logger:
    """
    Create a child logger for a specific filter module
    """
    # Sanitize filter name for logger name
    safe_name = filter_name.lower().replace(' ', '_').replace('-', '_')
    filter_logger = main_logger.getChild(f"filter.{safe_name}")
    
    return filter_logger


class ProgressTracker:
    """Helper class for tracking and logging progress through operations"""
    
    def __init__(self, logger: logging.Logger, operation_name: str, total_items: int):
        self.logger = logger
        self.operation_name = operation_name
        self.total_items = total_items
        self.processed_items = 0
        self.start_time = datetime.now()
        
        # Log intervals (log every X items or X%)
        self.log_every_n = max(1, total_items // 20)  # Log every 5%
        self.log_every_n = min(self.log_every_n, 100)  # But at least every 100 items
        
        self.logger.info(f"🚀 Starting {operation_name} for {total_items} items")
    
    def update(self, increment: int = 1):
        """Update progress and log if needed"""
        self.processed_items += increment
        
        # Log at intervals
        if self.processed_items % self.log_every_n == 0 or self.processed_items == self.total_items:
            percent = (self.processed_items / self.total_items) * 100
            elapsed = datetime.now() - self.start_time
            
            if self.processed_items == self.total_items:
                self.logger.info(f"✅ {self.operation_name} completed: {self.processed_items}/{self.total_items} in {elapsed}")
            else:
                self.logger.debug(f"📊 {self.operation_name} progress: {self.processed_items}/{self.total_items} ({percent:.1f}%)")
    
    def log_batch_result(self, batch_num: int, batch_size: int, success_count: int):
        """Log results for a batch operation"""
        self.logger.debug(f"   Batch {batch_num}: {success_count}/{batch_size} successful")


class FilterMetrics:
    """Track and log metrics for filter operations"""
    
    def __init__(self, logger: logging.Logger, filter_name: str):
        self.logger = logger
        self.filter_name = filter_name
        self.start_time = datetime.now()
        
        # Metrics
        self.people_with_tags = 0
        self.people_after_exclusions = 0
        self.people_after_banned_filter = 0
        self.people_assigned = 0
        self.api_calls_made = 0
        self.errors_encountered = 0
    
    def log_step(self, step_name: str, count: int, note: str = ""):
        """Log a step in the filter process"""
        setattr(self, step_name.lower().replace(' ', '_'), count)
        note_str = f" ({note})" if note else ""
        self.logger.info(f"   📊 {step_name}: {count} people{note_str}")
    
    def increment_api_calls(self):
        """Track API call count"""
        self.api_calls_made += 1
    
    def increment_errors(self):
        """Track error count"""
        self.errors_encountered += 1
    
    def log_final_summary(self):
        """Log final metrics summary"""
        duration = datetime.now() - self.start_time
        
        self.logger.info(f"\n📈 {self.filter_name} - Final Metrics:")
        self.logger.info(f"   ⏱️  Duration: {duration}")
        self.logger.info(f"   👥 People with tags: {self.people_with_tags}")
        self.logger.info(f"   🛤️  After exclusions: {self.people_after_exclusions}")
        self.logger.info(f"   🚫 After banned filter: {self.people_after_banned_filter}")
        self.logger.info(f"   ✅ Successfully assigned: {self.people_assigned}")
        self.logger.info(f"   🔗 API calls made: {self.api_calls_made}")
        if self.errors_encountered > 0:
            self.logger.info(f"   ❌ Errors encountered: {self.errors_encountered}")


def log_filter_start(logger: logging.Logger, filter_name: str, config: dict):
    """Log the start of a filter with its configuration"""
    logger.info(f"\n🎯 {filter_name}")
    logger.info("=" * 50)
    logger.info(f"Description: {config.get('description', 'N/A')}")
    logger.info(f"Target Path: {config.get('target_path_id')} (Step: {config.get('target_step_id')})")
    logger.info(f"Tag Count: {len(config.get('tag_ids', []))}")


def log_filter_completion(logger: logging.Logger, filter_name: str, result: dict):
    """Log the completion of a filter"""
    status = "✅ SUCCESS" if result.get('success', False) else "❌ FAILED"
    logger.info(f"\n{status} - {filter_name}")
    
    if result.get('success'):
        logger.info(f"   People processed: {result.get('people_count', 0)}")
        logger.info(f"   People assigned: {result.get('assigned_count', 0)}")
        if result.get('csv_filename'):
            logger.info(f"   Report saved: {result['csv_filename']}")
    else:
        logger.error(f"   Error: {result.get('error', 'Unknown error')}")


def log_system_info(logger: logging.Logger):
    """Log system information at the start of a run"""
    logger.info("🖥️  System Information:")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Working directory: {os.getcwd()}")
    logger.info(f"   Log level: {logger.level}")


def setup_cloud_function_logging():
    """
    Set up logging specifically for Google Cloud Functions
    (Simpler setup since Cloud Functions handle log collection)
    """
    logger = logging.getLogger("cf_nightly_runner")
    logger.setLevel(logging.INFO)
    
    # Cloud Functions prefer structured logging to stdout
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


# Convenience function for quick setup
def get_logger(name: str = "nb_filter", level: str = "INFO") -> logging.Logger:
    """Get a simple logger for testing/development"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only set up if not already configured
        logger.setLevel(getattr(logging, level.upper()))
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger