"""
Access Logger Middleware for Flask

Provides comprehensive HTTP request/response logging with:
- Automatic request/response tracking
- Sensitive data filtering
- Response time tracking
- Production-optimized performance
"""

import time
import logging
import re
from typing import Optional, Dict, Any
from flask import request, g, has_request_context
from flask_login import current_user
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


# Sensitive field patterns to filter from logs
SENSITIVE_PATTERNS = {
    'password': re.compile(r'password', re.IGNORECASE),
    'token': re.compile(r'(token|api_key|secret)', re.IGNORECASE),
    'credit_card': re.compile(r'(card|cvv|pin)', re.IGNORECASE),
    'auth': re.compile(r'(authorization|bearer)', re.IGNORECASE),
}

# Routes that should NOT be logged (to reduce noise)
EXCLUDE_ROUTES = {
    '/static',
    '/uploads',
}

# Routes that should not log request/response body (to save disk space)
EXCLUDE_BODY_LOGGING = {
    '/api/upload',
    '/api/file',
}


def get_client_ip() -> str:
    """
    Get the client IP address, accounting for proxies.
    
    Checks X-Forwarded-For header (for proxies like Nginx, CloudFlare)
    Falls back to request.remote_addr
    """
    if not has_request_context():
        return None
    
    # Check for X-Forwarded-For (set by reverse proxies)
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # X-Forwarded-For can be a comma-separated list, take the first
        return x_forwarded_for.split(',')[0].strip()
    
    # Check for X-Real-IP (used by some proxies)
    x_real_ip = request.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip
    
    # Fall back to request.remote_addr
    return request.remote_addr


def filter_sensitive_data(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
    """
    Recursively filter sensitive data from request/response data.
    
    Replaces values of sensitive keys with '***REDACTED***'
    
    Args:
        data: Dictionary to filter
        depth: Recursion depth (max 3 to prevent infinite recursion)
    
    Returns:
        Filtered dictionary
    """
    if depth > 3 or not isinstance(data, dict):
        return data
    
    filtered = {}
    for key, value in data.items():
        # Check if key matches any sensitive pattern
        is_sensitive = any(pattern.search(key) for pattern in SENSITIVE_PATTERNS.values())
        
        if is_sensitive:
            filtered[key] = '***REDACTED***'
        elif isinstance(value, dict):
            # Recursively filter nested dicts
            filtered[key] = filter_sensitive_data(value, depth + 1)
        elif isinstance(value, (list, tuple)):
            # Filter items in lists/tuples
            filtered[key] = [
                filter_sensitive_data(item, depth + 1) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            filtered[key] = value
    
    return filtered


def should_log_route() -> bool:
    """Determine if the current route should be logged."""
    if not has_request_context():
        return False
    
    path = request.path.lower()
    
    # Skip static files and uploads
    for exclude in EXCLUDE_ROUTES:
        if path.startswith(exclude):
            return False
    
    return True


def get_endpoint_name() -> str:
    """Get the Flask endpoint name, or the path if endpoint is not available."""
    try:
        return request.endpoint or request.path
    except Exception:
        return request.path


class AccessLoggerMiddleware:
    """
    Middleware for comprehensive HTTP request/response logging.
    
    Usage:
        app = Flask(__name__)
        # ... other setup ...
        logger_middleware = AccessLoggerMiddleware(app)
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
            
            # Log asynchronously to avoid blocking response
            # We'll do a simple sync write here; for production scale, use task queue
            self._log_to_database(
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
    
    def _log_to_database(
        self,
        user_id: Optional[int],
        http_method: str,
        endpoint: str,
        ip_address: str,
        status_code: int,
        response_time_ms: int,
    ):
        """
        Write access log to database.
        
        Wrapped in a try-except to prevent logging errors from breaking the app.
        For production with high traffic, consider:
        - Async task queue (Celery)
        - Direct database connection pool
        - Buffer + batch writes
        """
        try:
            from app import db
            from models import AccessLog
            
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
        
        except Exception as e:
            # Log to file as fallback
            logger.error(
                f"Failed to log to database: {e}. "
                f"Request: {http_method} {endpoint} {status_code}",
                exc_info=False
            )
            db.session.rollback()


def setup_access_logger(app):
    """
    Convenience function to set up the access logger middleware.
    
    Should be called after app initialization but before route imports.
    
    Usage:
        from access_logger import setup_access_logger
        
        app = Flask(__name__)
        # ... config ...
        setup_access_logger(app)
        # ... other setup ...
    """
    middleware = AccessLoggerMiddleware(app)
    return middleware
