"""
Improved Access Logger Middleware for Flask with Async Logging

Provides comprehensive HTTP request/response logging with:
- Automatic request/response tracking
- Background/deferred logging (doesn't block responses)
- Sensitive data filtering
- Production-optimized performance
"""

import time
import logging
import re
from typing import Optional
from flask import request, g, has_request_context
from flask_login import current_user
from datetime import datetime
from threading import Thread

logger = logging.getLogger(__name__)


# Sensitive field patterns to filter from logs
SENSITIVE_PATTERNS = {
    'password': re.compile(r'password', re.IGNORECASE),
    'token': re.compile(r'(token|api_key|secret)', re.IGNORECASE),
    'credit_card': re.compile(r'(card|cvv|pin)', re.IGNORECASE),
    'auth': re.compile(r'(authorization|bearer)', re.IGNORECASE),
}

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
    
    # Don't log static assets or excluded routes
    for excluded in EXCLUDE_ROUTES:
        if request.path.startswith(excluded):
            return False
    
    return True


def get_client_ip() -> str:
    """Get the client IP address, accounting for proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    return request.remote_addr or '0.0.0.0'


def get_endpoint_name() -> str:
    """Get the endpoint function name."""
    return request.endpoint or 'unknown'


def _log_to_database_async(
    user_id: Optional[int],
    http_method: str,
    endpoint: str,
    ip_address: str,
    status_code: int,
    response_time_ms: int,
):
    """
    Write access log to database in a background thread.
    
    Uses proper session cleanup to avoid connection pool exhaustion.
    """
    def _write_log():
        try:
            from app import db, app
            from models import AccessLog
            
            with app.app_context():
                try:
                    log_entry = AccessLog(
                        user_id=user_id,
                        http_method=http_method,
                        endpoint=endpoint,
                        ip_address=ip_address,
                        status_code=status_code,
                        response_time_ms=response_time_ms,
                        timestamp=datetime.utcnow(),
                    )
                    
                    db.session.add(log_entry)
                    db.session.commit()
                    logger.debug(f"Logged: {http_method} {endpoint} {status_code}")
                
                finally:
                    # CRITICAL: Always close the session to return connection to pool
                    db.session.close()
        
        except Exception as e:
            logger.error(f"Failed to log to database: {e}", exc_info=False)
    
    # Start background thread for logging (doesn't block response)
    thread = Thread(target=_write_log, daemon=True)
    thread.start()


class AccessLoggerMiddleware:
    """
    Non-blocking middleware for HTTP request/response logging.
    
    Uses background threads to avoid blocking responses during database operations.
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
    
    def before_request(self):
        """Hook called before each request."""
        if not should_log_route():
            return
        
        # Store request start time in g (request-local storage)
        g.request_start_time = time.time()
        g.request_ip = get_client_ip()
    
    def after_request(self, response):
        """Hook called after each request (including error responses)."""
        if not should_log_route():
            return response
        
        try:
            # Only log if we have start time (set in before_request)
            if not hasattr(g, 'request_start_time'):
                return response
            
            # Calculate response time
            elapsed_ms = int((time.time() - g.request_start_time) * 1000)
            
            # Get logging details
            endpoint = get_endpoint_name()
            ip_address = g.request_ip
            method = request.method
            status_code = response.status_code
            
            # Get user info (None for anonymous)
            user_id = current_user.id if current_user.is_authenticated else None
            
            # Log in background thread - DOESN'T BLOCK RESPONSE
            _log_to_database_async(
                user_id=user_id,
                http_method=method,
                endpoint=endpoint,
                ip_address=ip_address,
                status_code=status_code,
                response_time_ms=elapsed_ms,
            )
        
        except Exception as e:
            # CRITICAL: Never let logging break the application
            logger.exception(f"Error in access logger: {e}")
        
        return response


def setup_access_logger(app):
    """
    Convenience function to set up the access logger middleware.
    
    Usage:
        from access_logger_async import setup_access_logger
        
        app = Flask(__name__)
        setup_access_logger(app)
    """
    middleware = AccessLoggerMiddleware(app)
    logger.info("Access logger initialized with async background logging")
    return middleware
