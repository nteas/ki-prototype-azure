import os
import logging
import sys
from opencensus.ext.azure.log_exporter import AzureLogHandler

# Level should be one of https://docs.python.org/3/library/logging.html#logging-levels
handlers = [logging.StreamHandler(sys.stdout)]
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", None):
    handlers.append(AzureLogHandler(connection_string=os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"]))

logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", "INFO"), handlers=handlers)
logger = logging.getLogger(__name__)
