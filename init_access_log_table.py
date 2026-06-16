#!/usr/bin/env python
"""
Simple direct SQL migration to create access_log table.
"""
import os
from dotenv import load_dotenv
import pymysql

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Parse MySQL connection string
if 'mysql+pymysql://' in DATABASE_URL:
    parts = DATABASE_URL.replace('mysql+pymysql://', '').split('@')
    user_pass = parts[0].split(':')
    host_db = parts[1].split('/')
    
    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_db[0].split(':')[0]
    port = int(host_db[0].split(':')[1]) if ':' in host_db[0] else 3306
    database = host_db[1]
    
    print(f"Connecting to {user}@{host}:{port}/{database}\n")
    
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'access_log'")
        exists = cursor.fetchone()
        
        if exists:
            print("✓ access_log table already exists")
            cursor.close()
            connection.close()
            exit(0)
        
        print("Creating access_log table...")
        
        # Create the table
        create_sql = """
        CREATE TABLE access_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            user_id INT,
            http_method VARCHAR(10) NOT NULL,
            endpoint VARCHAR(255) NOT NULL,
            ip_address VARCHAR(45),
            status_code INT,
            response_time_ms INT,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
            INDEX ix_access_log_timestamp (timestamp),
            INDEX ix_access_log_user_id (user_id),
            INDEX ix_access_log_http_method (http_method),
            INDEX ix_access_log_endpoint (endpoint),
            INDEX ix_access_log_status_code (status_code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_sql)
        connection.commit()
        
        print("✓ access_log table created successfully")
        
        # Verify
        cursor.execute("SHOW TABLES LIKE 'access_log'")
        if cursor.fetchone():
            print("✓ Table verified")
        
        print("\nTable structure:")
        cursor.execute("DESC access_log")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        print("\n✓ Migration completed successfully!")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        exit(1)
else:
    print("✗ Could not parse DATABASE_URL")
    print(f"  URL: {DATABASE_URL}")
    exit(1)
