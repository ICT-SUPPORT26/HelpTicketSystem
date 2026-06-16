"""
Database migration for access_log table
Adds new fields and restructures the table for comprehensive HTTP logging

This migration handles:
1. Renames 'path' column to 'endpoint'
2. Renames 'method' column to 'http_method'  
3. Removes 'action' column (no longer needed)
4. Adds 'status_code' column
5. Adds 'response_time_ms' column
6. Ensures proper indexes for performance
7. Renames table from 'access_log' to match SQLAlchemy's naming
"""

import os
from dotenv import load_dotenv

def migrate_access_log_table():
    """
    Apply migration to access_log table.
    
    Can be run with:
        python -c "from migrate_access_log import migrate_access_log_table; migrate_access_log_table()"
        or
        python migrate_access_log.py
    """
    load_dotenv()
    
    # Import app to get context
    from app import app, db
    
    with app.app_context():
        try:
            connection = db.engine.raw_connection()
            cursor = connection.cursor()
            
            db_type = str(db.engine.url).split('+')[0].lower()
            
            print(f"Detected database type: {db_type}")
            print("Starting migration...")
            
            # PostgreSQL migration
            if db_type in ('postgresql', 'postgres'):
                migration_steps_pg = [
                    # Step 1: Add new columns if they don't exist
                    """
                    ALTER TABLE access_log
                    ADD COLUMN IF NOT EXISTS status_code INTEGER;
                    """,
                    
                    """
                    ALTER TABLE access_log
                    ADD COLUMN IF NOT EXISTS response_time_ms INTEGER;
                    """,
                    
                    """
                    ALTER TABLE access_log
                    ADD COLUMN IF NOT EXISTS http_method VARCHAR(10);
                    """,
                    
                    """
                    ALTER TABLE access_log
                    ADD COLUMN IF NOT EXISTS endpoint VARCHAR(255);
                    """,
                    
                    # Step 2: Copy data from old columns to new columns
                    """
                    UPDATE access_log SET http_method = method WHERE http_method IS NULL AND method IS NOT NULL;
                    """,
                    
                    """
                    UPDATE access_log SET endpoint = path WHERE endpoint IS NULL AND path IS NOT NULL;
                    """,
                    
                    # Step 3: Make columns not nullable after data is populated
                    """
                    ALTER TABLE access_log ALTER COLUMN http_method SET NOT NULL;
                    """,
                    
                    """
                    ALTER TABLE access_log ALTER COLUMN endpoint SET NOT NULL;
                    """,
                    
                    # Step 4: Create indexes for performance
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_http_method ON access_log (http_method);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_endpoint ON access_log (endpoint);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_status_code ON access_log (status_code);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_timestamp ON access_log (timestamp);
                    """,
                ]
                
                for step in migration_steps_pg:
                    try:
                        cursor.execute(step)
                        connection.commit()
                        print(f"✓ {step.strip()[:60]}...")
                    except Exception as e:
                        print(f"⚠ Step skipped: {e}")
                        connection.rollback()
            
            # MySQL migration
            elif db_type in ('mysql', 'mysql+pymysql'):
                migration_steps_mysql = [
                    # Step 1: Add new columns if they don't exist
                    """
                    ALTER TABLE access_log
                    ADD COLUMN `status_code` INT NULL;
                    """,
                    
                    """
                    ALTER TABLE access_log
                    ADD COLUMN `response_time_ms` INT NULL;
                    """,
                    
                    """
                    ALTER TABLE access_log
                    ADD COLUMN `http_method` VARCHAR(10) NULL;
                    """,
                    
                    """
                    ALTER TABLE access_log
                    ADD COLUMN `endpoint` VARCHAR(255) NULL;
                    """,
                    
                    # Step 2: Copy data from old columns to new columns
                    """
                    UPDATE access_log SET `http_method` = `method` 
                    WHERE `http_method` IS NULL AND `method` IS NOT NULL;
                    """,
                    
                    """
                    UPDATE access_log SET `endpoint` = `path`
                    WHERE `endpoint` IS NULL AND `path` IS NOT NULL;
                    """,
                    
                    # Step 3: Modify columns to NOT NULL
                    """
                    ALTER TABLE access_log 
                    MODIFY COLUMN `http_method` VARCHAR(10) NOT NULL;
                    """,
                    
                    """
                    ALTER TABLE access_log
                    MODIFY COLUMN `endpoint` VARCHAR(255) NOT NULL;
                    """,
                    
                    # Step 4: Create indexes for performance
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_http_method ON access_log (`http_method`);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_endpoint ON access_log (`endpoint`);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_status_code ON access_log (`status_code`);
                    """,
                ]
                
                for step in migration_steps_mysql:
                    try:
                        cursor.execute(step)
                        connection.commit()
                        print(f"✓ {step.strip()[:60]}...")
                    except Exception as e:
                        print(f"⚠ Step skipped: {e}")
                        connection.rollback()
            
            # SQLite migration (for development/testing)
            elif db_type == 'sqlite':
                migration_steps_sqlite = [
                    # SQLite: Drop and recreate table (no ALTER COLUMN in SQLite)
                    """
                    CREATE TABLE IF NOT EXISTS access_log_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        user_id INTEGER,
                        http_method VARCHAR(10) NOT NULL,
                        endpoint VARCHAR(255) NOT NULL,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(512),
                        status_code INTEGER,
                        response_time_ms INTEGER,
                        FOREIGN KEY (user_id) REFERENCES user(id)
                    );
                    """,
                    
                    """
                    INSERT INTO access_log_new 
                    SELECT id, timestamp, user_id, 
                           COALESCE(method, 'UNKNOWN') as http_method,
                           COALESCE(path, '/unknown') as endpoint,
                           ip_address, user_agent, NULL, NULL
                    FROM access_log;
                    """,
                    
                    """
                    DROP TABLE IF EXISTS access_log;
                    """,
                    
                    """
                    ALTER TABLE access_log_new RENAME TO access_log;
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_user_id ON access_log(user_id);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_timestamp ON access_log(timestamp);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_http_method ON access_log(http_method);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_endpoint ON access_log(endpoint);
                    """,
                    
                    """
                    CREATE INDEX IF NOT EXISTS ix_access_log_status_code ON access_log(status_code);
                    """,
                ]
                
                for step in migration_steps_sqlite:
                    try:
                        cursor.execute(step)
                        connection.commit()
                        print(f"✓ {step.strip()[:60]}...")
                    except Exception as e:
                        print(f"⚠ Step skipped: {e}")
                        connection.rollback()
            
            cursor.close()
            connection.close()
            print("\nMigration completed successfully!")
        
        except Exception as e:
            print(f"\nMigration failed: {e}")
            raise


if __name__ == '__main__':
    migrate_access_log_table()
