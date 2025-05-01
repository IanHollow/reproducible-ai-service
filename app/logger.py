import logging
import sys
from app.config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Log to console
        # Optionally add FileHandler here
        # logging.FileHandler("app.log")
    ],
)

# Get the logger instance
logger = logging.getLogger(__name__)


def get_logger():
    return logger
