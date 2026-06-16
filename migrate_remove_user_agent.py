#!/usr/bin/env python
"""
Simple direct migration to remove user_agent column from access_log table.
"""
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Parse MySQL connection string
if 'mysql+pymysql://' in DATABASE_URL:
    # Format: mysql+pymysql://user:pass@host:port/database
    parts = DATABASE_URL.replace('mysql+pymysql://', '').split('@')
    user_pass = parts[0].split(':')
    host_db = parts[1].split('/')
    
    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_db[0].split(':')[0]
    port = int(host_db[0].split(':')[1]) if ':' in host_db[0] else 3306
    database = host_db[1]
    
    print(f"Connecting to {user}@{host}:{port}/{database}")
    
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM access_log LIKE 'user_agent'")
        exists = cursor.fetchone()
        
        if not exists:
            print("ⓘ Column 'user_agent' does not exist (already removed or never existed)")
            cursor.close()
            connection.close()
            exit(0)
        
        # Drop the column
        print("Removing user_agent column...")
        cursor.execute("ALTER TABLE access_log DROP COLUMN user_agent")
        connection.commit()
        
        print("✓ Migration completed successfully!")
        print("  - Removed user_agent column from access_log table")
        print("  - Storage savings: ~512 bytes per log entry")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        exit(1)
else:
    print("✗ Could not parse DATABASE_URL")
    print(f"  URL: {DATABASE_URL}")
    exit(1)
