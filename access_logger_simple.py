"""
Lightweight Access Logger Middleware using Queue-Based Buffering

Non-blocking, efficient logging that uses an in-memory queue to batch writes.
"""

import time
import logging
from typing import Optional
from flask import request, g, has_request_context
from flask_login import current_user

logger = logging.getLogger(__name__)

# Routes that should NOT be logged
EXCLUDE_ROUTES = {
    '/static',
    '/uploads',
    '/files',
}


def should_log_route() -> bool:
    """Check if the current route should be logged."""
    if not has_request_context():
        return False
    
    for excluded in EXCLUDE_ROUTES:
        if request.path.startswith(excluded):
            return False
    
    return True


def get_client_ip() -> str:
    """Get the client IP address, accounting for proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    return request.remote_addr or '0.0.0.0'


class AccessLoggerMiddleware:
    """
    Efficient middleware using queue-based access logging.
    
    Logs are queued immediately (very fast) and written in batches by background thread.
    """
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with a Flask app."""
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Start the log flusher thread
        from access_log_queue import start_access_log_flusher
        start_access_log_flusher(app)
    
    def before_request(self):
        """Hook called before each request."""
        if not should_log_route():
            return
        
        g.request_start_time = time.time()
        g.request_ip = get_client_ip()
    
    def after_request(self, response):
        """Hook called after each request."""
        if not should_log_route():
            return response
        
        try:
            if not hasattr(g, 'request_start_time'):
                return response
            
            elapsed_ms = int((time.time() - g.request_start_time) * 1000)
            
            endpoint = request.endpoint or 'unknown'
            ip_address = g.request_ip
            method = request.method
            status_code = response.status_code
            user_id = current_user.id if current_user.is_authenticated else None
            
            # Queue the log for batch writing (very fast, non-blocking)
            from access_log_queue import queue_access_log
            queue_access_log(
                user_id=user_id,
                http_method=method,
                endpoint=endpoint,
                ip_address=ip_address,
                status_code=status_code,
                response_time_ms=elapsed_ms,
            )
        
        except Exception as e:
            logger.exception(f"Error queuing access log: {e}")
        
        return response


def setup_access_logger(app):
    """Initialize the queue-based access logger."""
    middleware = AccessLoggerMiddleware(app)
    logger.info("Queue-based access logger initialized")
    return middleware
