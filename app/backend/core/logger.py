import os
import logging
import sys

logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", "INFO"), handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)
