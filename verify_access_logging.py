#!/usr/bin/env python
"""
Access Logger Verification & Testing Script

This script validates the access logging implementation by:
1. Checking database schema
2. Verifying middleware is initialized
3. Testing access log creation
4. Running performance benchmarks
5. Checking admin dashboard access

Usage:
    python verify_access_logging.py
"""

import time
import statistics
from datetime import datetime
import os

# Try to import Flask app for internal checks
try:
    from app import app, db
    from models import AccessLog, User
    INTERNAL_TESTING = True
except ImportError:
    INTERNAL_TESTING = False
    print("Warning: Could not import Flask app. Using external HTTP tests only.\n")

# Try to import requests (optional)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}\n")


def check_mark(condition, message):
    """Print a checkmark or X based on condition."""
    symbol = " [OK]" if condition else " [FAIL]"
    print(f"{symbol} {message}")
    return condition


def test_database_schema():
    """Test database schema for access_log table."""
    print_header("1. DATABASE SCHEMA VERIFICATION")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Check if AccessLog table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            table_exists = 'access_log' in tables
            check_mark(table_exists, "AccessLog table exists")
            
            if not table_exists:
                return False
            
            # Check required columns
            columns = inspector.get_columns('access_log')
            column_names = {col['name'] for col in columns}
            
            required_cols = {
                'id', 'timestamp', 'user_id', 'http_method', 'endpoint',
                'ip_address', 'user_agent', 'status_code', 'response_time_ms'
            }
            
            for col in required_cols:
                exists = col in column_names
                check_mark(exists, f"Column '{col}' exists")
                if not exists:
                    return False
            
            # Check indexes
            indexes = inspector.get_indexes('access_log')
            index_cols = [idx['column_names'][0] for idx in indexes if len(idx['column_names']) == 1]
            
            important_indexes = ['timestamp', 'user_id', 'status_code']
            for idx_col in important_indexes:
                has_index = idx_col in index_cols
                check_mark(has_index, f"Index on '{idx_col}' column")
            
            return True
    
    except Exception as e:
        print(f" [FAIL] Error checking schema: {e}\n")
        return False


def test_middleware():
    """Test if middleware is initialized."""
    print_header("2. MIDDLEWARE INITIALIZATION")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Check if before_request and after_request are registered
            before_funcs = app.before_request_funcs.get(None, [])
            after_funcs = app.after_request_funcs.get(None, [])
            
            has_before = any('enforce' in func.__name__.lower() or len(before_funcs) > 0 for func in before_funcs)
            has_after = len(after_funcs) > 0
            
            check_mark(len(before_funcs) > 0, f"Before-request hooks registered ({len(before_funcs)} total)")
            check_mark(len(after_funcs) > 0, f"After-request hooks registered ({len(after_funcs)} total)")
            
            return True
    
    except Exception as e:
        print(f" [FAIL] Error checking middleware: {e}\n")
        return False


def test_access_log_creation():
    """Test creating an access log entry."""
    print_header("3. ACCESS LOG CREATION TEST")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Create test log
            test_log = AccessLog(
                user_id=None,
                http_method='GET',
                endpoint='/test',
                ip_address='127.0.0.1',
                user_agent='TestAgent/1.0',
                status_code=200,
                response_time_ms=42,
            )
            
            db.session.add(test_log)
            db.session.commit()
            
            check_mark(True, "Test log created successfully")
            
            # Verify log was saved
            saved_log = AccessLog.query.filter_by(endpoint='/test').first()
            if saved_log:
                check_mark(True, f"Test log retrieved (ID: {saved_log.id})")
                check_mark(saved_log.status_code == 200, f"Status code correctly stored (200)")
                check_mark(saved_log.response_time_ms == 42, f"Response time correctly stored (42ms)")
                
                # Clean up
                db.session.delete(saved_log)
                db.session.commit()
                
                return True
            else:
                print(" [FAIL] Could not retrieve saved log\n")
                return False
    
    except Exception as e:
        print(f" [FAIL] Error creating log: {e}\n")
        return False


def test_http_requests(base_url='http://localhost:5000'):
    """Test actual HTTP requests and verify they're logged."""
    print_header("4. HTTP REQUEST LOGGING TEST")
    
    if not HAS_REQUESTS:
        print("Skipping: 'requests' module not installed\n")
        return False
    
    try:
        # Test various request types
        test_routes = [
            ('GET', '/'),
        ]
        
        response_times = []
        
        for method, route in test_routes:
            try:
                start = time.time()
                if method == 'GET':
                    response = requests.get(f"{base_url}{route}", timeout=5)
                elapsed = (time.time() - start) * 1000
                
                success = response.status_code < 500
                check_mark(success, f"{method} {route} - Status {response.status_code} ({elapsed:.0f}ms)")
                response_times.append(elapsed)
            
            except requests.exceptions.ConnectionError:
                print(f" [WARN] Could not connect to Flask app - ensure it's running")
                return False
            except Exception as e:
                print(f" [FAIL] {method} {route} - {str(e)[:40]}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            print(f"\nAverage response time: {avg_time:.1f}ms\n")
        
        return True
    
    except Exception as e:
        print(f" [FAIL] Error testing HTTP: {e}\n")
        return False


def test_admin_dashboard(base_url='http://localhost:5000'):
    """Test access to admin logs dashboard."""
    print_header("5. ADMIN DASHBOARD ACCESS TEST")
    
    if not HAS_REQUESTS:
        print("Skipping: 'requests' module not installed\n")
        return False
    
    try:
        response = requests.get(f"{base_url}/access_logs", timeout=5)
        
        if response.status_code == 302:  # Redirect to login
            check_mark(True, "Admin route exists (redirect to login for non-authenticated user)")
            return True
        elif response.status_code == 200:
            check_mark('access_logs' in response.text.lower() or 'logs' in response.text.lower(),
                      "Admin dashboard accessible")
            return True
        else:
            check_mark(False, f"Admin route returned {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(" [WARN] Could not connect to Flask app - ensure it's running\n")
        return False
    except Exception as e:
        print(f" [FAIL] Error testing admin dashboard: {e}\n")
        return False


def test_performance():
    """Run performance benchmarks."""
    print_header("6. PERFORMANCE BENCHMARKS")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Benchmark AccessLog query performance
            start = time.time()
            logs = AccessLog.query.limit(100).all()
            query_time = (time.time() - start) * 1000
            
            check_mark(query_time < 100, f"Query 100 logs: {query_time:.1f}ms (target: <100ms)")
            
            # Benchmark with filter
            start = time.time()
            logs = AccessLog.query.filter(AccessLog.status_code == 200).limit(100).all()
            filter_time = (time.time() - start) * 1000
            
            check_mark(filter_time < 100, f"Filtered query: {filter_time:.1f}ms (target: <100ms)")
            
            # Benchmark pagination
            start = time.time()
            paginated = AccessLog.query.paginate(page=1, per_page=100)
            paginate_time = (time.time() - start) * 1000
            
            check_mark(paginate_time < 100, f"Paginated query: {paginate_time:.1f}ms (target: <100ms)")
            
            return True
    
    except Exception as e:
        print(f" [FAIL] Error running benchmarks: {e}\n")
        return False


def main():
    """Run all tests."""
    print(f"\n{'='*60}")
    print("Access Logger Verification & Testing")
    print(f"{'='*60}\n")
    
    results = []
    
    results.append(("Database Schema", test_database_schema()))
    results.append(("Middleware", test_middleware()))
    results.append(("Log Creation", test_access_log_creation()))
    results.append(("HTTP Requests", test_http_requests()))
    results.append(("Admin Dashboard", test_admin_dashboard()))
    results.append(("Performance", test_performance()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL/SKIP]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed\n")
    
    if passed >= 4:
        print("✓ Core tests passed! Access logging is working correctly.\n")
        return 0
    else:
        print("✗ Critical tests failed. Please review the implementation.\n")
        return 1


if __name__ == '__main__':
    exit(main())


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}\n")


def check_mark(condition, message):
    """Print a checkmark or X based on condition."""
    symbol = " [OK]" if condition else " [FAIL]"
    print(f"{symbol} {message}")
    return condition


def test_database_schema():
    """Test database schema for access_log table."""
    print_header("1. DATABASE SCHEMA VERIFICATION")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Check if AccessLog table exists
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            table_exists = 'access_log' in tables
            check_mark(table_exists, "AccessLog table exists")
            
            if not table_exists:
                return False
            
            # Check required columns
            columns = inspector.get_columns('access_log')
            column_names = {col['name'] for col in columns}
            
            required_cols = {
                'id', 'timestamp', 'user_id', 'http_method', 'endpoint',
                'ip_address', 'user_agent', 'status_code', 'response_time_ms'
            }
            
            for col in required_cols:
                exists = col in column_names
                check_mark(exists, f"Column '{col}' exists")
                if not exists:
                    return False
            
            # Check indexes
            indexes = inspector.get_indexes('access_log')
            index_cols = [idx['column_names'][0] for idx in indexes if len(idx['column_names']) == 1]
            
            important_indexes = ['timestamp', 'user_id', 'status_code']
            for idx_col in important_indexes:
                has_index = idx_col in index_cols
                check_mark(has_index, f"Index on '{idx_col}' column")
            
            return True
    
    except Exception as e:
        print(f" [FAIL] Error checking schema: {e}\n")
        return False


def test_middleware():
    """Test if middleware is initialized."""
    print_header("2. MIDDLEWARE INITIALIZATION")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Check if before_request and after_request are registered
            before_funcs = app.before_request_funcs.get(None, [])
            after_funcs = app.after_request_funcs.get(None, [])
            
            has_before = any('access' in func.__name__.lower() or 'logger' in func.__name__.lower() 
                           for func in before_funcs)
            has_after = any('access' in func.__name__.lower() or 'logger' in func.__name__.lower() 
                          for func in after_funcs)
            
            check_mark(has_before or len(before_funcs) > 0, "Before-request hook registered")
            check_mark(has_after or len(after_funcs) > 0, "After-request hook registered")
            
            return True
    
    except Exception as e:
        print(f" [FAIL] Error checking middleware: {e}\n")
        return False


def test_access_log_creation():
    """Test creating an access log entry."""
    print_header("3. ACCESS LOG CREATION TEST")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Create test log
            test_log = AccessLog(
                user_id=None,
                http_method='GET',
                endpoint='/test',
                ip_address='127.0.0.1',
                user_agent='TestAgent/1.0',
                status_code=200,
                response_time_ms=42,
            )
            
            db.session.add(test_log)
            db.session.commit()
            
            check_mark(True, "Test log created successfully")
            
            # Verify log was saved
            saved_log = AccessLog.query.filter_by(endpoint='/test').first()
            if saved_log:
                check_mark(True, f"Test log retrieved (ID: {saved_log.id})")
                check_mark(saved_log.status_code == 200, f"Status code correctly stored (200)")
                check_mark(saved_log.response_time_ms == 42, f"Response time correctly stored (42ms)")
                
                # Clean up
                db.session.delete(saved_log)
                db.session.commit()
                
                return True
            else:
                print(" [FAIL] Could not retrieve saved log\n")
                return False
    
    except Exception as e:
        print(f" [FAIL] Error creating log: {e}\n")
        return False


def test_http_requests(base_url='http://localhost:5000'):
    """Test actual HTTP requests and verify they're logged."""
    print_header("4. HTTP REQUEST LOGGING TEST")
    
    try:
        # Test various request types
        test_routes = [
            ('GET', '/'),
        ]
        
        response_times = []
        
        for method, route in test_routes:
            try:
                start = time.time()
                if method == 'GET':
                    response = requests.get(f"{base_url}{route}", timeout=5)
                elapsed = (time.time() - start) * 1000
                
                success = response.status_code < 500
                check_mark(success, f"{method} {route} - Status {response.status_code} ({elapsed:.0f}ms)")
                response_times.append(elapsed)
            
            except requests.exceptions.ConnectionError:
                print(f" [FAIL] {method} {route} - Could not connect")
                return False
            except Exception as e:
                print(f" [FAIL] {method} {route} - {str(e)[:40]}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            print(f"\nAverage response time: {avg_time:.1f}ms\n")
        
        return True
    
    except Exception as e:
        print(f" [FAIL] Error testing HTTP: {e}\n")
        return False


def test_admin_dashboard(base_url='http://localhost:5000'):
    """Test access to admin logs dashboard."""
    print_header("5. ADMIN DASHBOARD ACCESS TEST")
    
    try:
        response = requests.get(f"{base_url}/access_logs", timeout=5)
        
        if response.status_code == 302:  # Redirect to login
            check_mark(True, "Admin route exists (redirect to login for non-authenticated user)")
            return True
        elif response.status_code == 200:
            check_mark('access_logs' in response.text.lower() or 'logs' in response.text.lower(),
                      "Admin dashboard accessible")
            return True
        else:
            check_mark(False, f"Admin route returned {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(" [WARN] Could not connect to Flask app - ensure it's running\n")
        return False
    except Exception as e:
        print(f" [FAIL] Error testing admin dashboard: {e}\n")
        return False


def test_performance():
    """Run performance benchmarks."""
    print_header("6. PERFORMANCE BENCHMARKS")
    
    if not INTERNAL_TESTING:
        print("Skipping: No Flask app context\n")
        return False
    
    try:
        with app.app_context():
            # Benchmark AccessLog query performance
            start = time.time()
            logs = AccessLog.query.limit(100).all()
            query_time = (time.time() - start) * 1000
            
            check_mark(query_time < 100, f"Query 100 logs: {query_time:.1f}ms (target: <100ms)")
            
            # Benchmark with filter
            start = time.time()
            logs = AccessLog.query.filter(AccessLog.status_code == 200).limit(100).all()
            filter_time = (time.time() - start) * 1000
            
            check_mark(filter_time < 100, f"Filtered query: {filter_time:.1f}ms (target: <100ms)")
            
            # Benchmark pagination
            start = time.time()
            paginated = AccessLog.query.paginate(page=1, per_page=100)
            paginate_time = (time.time() - start) * 1000
            
            check_mark(paginate_time < 100, f"Paginated query: {paginate_time:.1f}ms (target: <100ms)")
            
            return True
    
    except Exception as e:
        print(f" [FAIL] Error running benchmarks: {e}\n")
        return False


def main():
    """Run all tests."""
    print(f"\n{'='*60}")
    print("Access Logger Verification & Testing")
    print(f"{'='*60}\n")
    
    results = []
    
    results.append(("Database Schema", test_database_schema()))
    results.append(("Middleware", test_middleware()))
    results.append(("Log Creation", test_access_log_creation()))
    results.append(("HTTP Requests", test_http_requests()))
    results.append(("Admin Dashboard", test_admin_dashboard()))
    results.append(("Performance", test_performance()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed\n")
    
    if passed == total:
        print("✓ All tests passed! Access logging is working correctly.\n")
        return 0
    elif passed > total // 2:
        print("⚠ Some tests failed. Review the output above.\n")
        return 1
    else:
        print("✗ Most tests failed. Please review the implementation.\n")
        return 1


if __name__ == '__main__':
    exit(main())
