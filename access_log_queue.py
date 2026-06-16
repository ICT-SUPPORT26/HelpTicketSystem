"""
Simple In-Memory Queue Based Access Logger

Uses a thread-safe queue to buffer log entries and flush them periodically.
This avoids the connection pool exhaustion issues with per-request logging threads.
"""

import logging
import time
import atexit
from queue import Queue
from threading import Thread
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Global logging queue
_access_log_queue = Queue(maxsize=1000)  # Buffer up to 1000 entries
_logger_thread = None
_should_stop = False


def start_access_log_flusher(app):
    """Start the background thread that flushes access logs to database."""
    global _logger_thread
    
    def _flush_logs():
        """Periodically flush queued logs to database."""
        logs_to_write = []
        
        while not _should_stop:
            try:
                # Collect logs from queue (with timeout to avoid blocking forever)
                while len(logs_to_write) < 50:  # Batch up to 50 logs
                    try:
                        log_data = _access_log_queue.get(timeout=5)  # Wait max 5 seconds
                        logs_to_write.append(log_data)
                    except:
                        break  # Queue is empty or timeout
                
                # Write batch to database if we have any
                if logs_to_write:
                    with app.app_context():
                        try:
                            from extensions import db
                            from models import AccessLog
                            
                            for log_data in logs_to_write:
                                log_entry = AccessLog(**log_data)
                                db.session.add(log_entry)
                            
                            db.session.commit()
                            logger.debug(f"Flushed {len(logs_to_write)} access logs to database")
                            logs_to_write = []
                        
                        except Exception as e:
                            logger.error(f"Failed to flush access logs: {e}")
                            db.session.rollback()
                            logs_to_write = []
                        
                        finally:
                            db.session.close()
            
            except Exception as e:
                logger.error(f"Error in access log flusher: {e}")
                time.sleep(1)
    
    _logger_thread = Thread(target=_flush_logs, daemon=True)
    _logger_thread.start()
    logger.info("Access log flusher thread started")


def queue_access_log(
    user_id: Optional[int],
    http_method: str,
    endpoint: str,
    ip_address: str,
    status_code: int,
    response_time_ms: int,
):
    """
    Queue an access log entry for asynchronous writing.
    
    This is fast and non-blocking - just adds to an in-memory queue.
    """
    try:
        log_data = {
            'user_id': user_id,
            'http_method': http_method,
            'endpoint': endpoint,
            'ip_address': ip_address,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'timestamp': datetime.utcnow(),
        }
        
        # Non-blocking put - drops log if queue is full (overflow protection)
        _access_log_queue.put_nowait(log_data)
    except:
        # Queue is full - just skip this log to avoid blocking the response
        logger.warning("Access log queue full - skipping log entry")
