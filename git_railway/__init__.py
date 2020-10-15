import logging
import os


LOGGER = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
)
LOGGER.addHandler(handler)
LOGGER.setLevel(
    getattr(logging, os.environ.get("GIT_RAILWAY_DEBUG_LEVEL", "INFO").upper())
)
