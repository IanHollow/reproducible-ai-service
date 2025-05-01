import logging
import sys
import json
import os
from app.config import settings

# Ensure logs directory exists
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)


# Define JSON Formatter (REQ-028)
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            # Add other fields from the log record if needed
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        # Include exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        # Include extra fields passed to the logger without static‐analysis errors
        extra_data = getattr(record, "extra_data", None)
        if isinstance(extra_data, dict):
            log_record.update(extra_data)

        return json.dumps(log_record)


# Configure Logger
def get_logger(name="AIContentGuard"):
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL.upper())

    # Prevent duplicate handlers if logger already configured
    if logger.hasHandlers():
        return logger

    # Console Handler (Standard Format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # JSONL File Handler (REQ-028)
    if settings.LOG_TO_FILE:
        log_file_path = os.path.join(LOGS_DIR, "output.jsonl")
        file_handler = logging.FileHandler(log_file_path, mode="a")  # Append mode
        json_formatter = JsonFormatter()
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to JSONL file: {log_file_path}")

    return logger


# Example usage:
# logger = get_logger()
# logger.info("This is an info message")
# logger.warning("This is a warning")
# logger.error("This is an error", extra={"request_id": "123", "details": {"key": "value"}})
