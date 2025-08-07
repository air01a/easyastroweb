import logging
from services.configurator import CONFIG

log_level = CONFIG["global"].get("log_level", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)
logger.info("Logger initialized with level: %s", log_level)