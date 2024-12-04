import logging
import threading
from .events import EventStream

logger = logging.getLogger(__name__)

def start_event_stream():
    """Start the event stream in a separate thread"""
    try:
        event_stream = EventStream()
        logger.info("Event stream started successfully")
    except Exception as e:
        logger.error(f"Failed to start event stream: {e}")