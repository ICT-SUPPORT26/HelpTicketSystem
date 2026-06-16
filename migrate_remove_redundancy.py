#!/usr/bin/env python
"""
Migration script to remove data redundancy from access_log table.

Changes:
- Removes unused user_agent column (512 bytes per log entry)
- Reduces database size and improves query performance
"""

import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Get database connection string
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///helpticket.db')

def detect_database_type():
    """Detect database type from connection string."""
    parsed = urlparse(DATABASE_URL)
    
    # Check the scheme first
    scheme = parsed.scheme.lower() if parsed.scheme else ''
    
    if 'mysql' in scheme or 'mariadb' in scheme:
        return 'mysql'
    elif 'postgresql' in scheme or 'postgres' in scheme:
        return 'postgresql'
    elif 'sqlite' in scheme:
        return 'sqlite'
    else:
        # Default: check if using Flask-SQLAlchemy
        print(f"Database URL scheme: {scheme}")
        return 'mysql' if scheme else 'sqlite'

def run_migration():
    """Execute migration to remove redundant user_agent column."""
    print("Starting migration...")
    
    try:
        from app import db, app
        from models import AccessLog
        
        with app.app_context():
            # Check if column exists
            inspector = db.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('access_log')]
            
            if 'user_agent' not in columns:
                print("ⓘ Column user_agent does not exist (already removed)")
                return True
            
            db_type = detect_database_type()
            print(f"Detected database type: {db_type}")
            
            if db_type == 'mysql':
                # MySQL: DROP COLUMN syntax
                sql = "ALTER TABLE access_log DROP COLUMN user_agent"
                print(f"Executing: {sql}")
                
                try:
                    db.session.execute(sql)
                    db.session.commit()
                    print("✓ Migration completed successfully!")
                    print("  - Removed user_agent column")
                    print("  - This reduces storage per log entry by 512 bytes")
                    return True
                except Exception as e:
                    if 'check that this column/key exists' in str(e) or 'Unknown column' in str(e):
                        print("ⓘ Column user_agent does not exist (already removed)")
                        return True
                    else:
                        raise
            
            elif db_type == 'postgresql':
                # PostgreSQL: DROP COLUMN syntax
                sql = "ALTER TABLE access_log DROP COLUMN user_agent"
                print(f"Executing: {sql}")
                
                try:
                    db.session.execute(sql)
                    db.session.commit()
                    print("✓ Migration completed successfully!")
                    print("  - Removed user_agent column")
                    print("  - This reduces storage per log entry by 512 bytes")
                    return True
                except Exception as e:
                    if 'does not exist' in str(e):
                        print("ⓘ Column user_agent does not exist (already removed)")
                        return True
                    else:
                        raise
            
            else:  # SQLite
                print("ℹ SQLite detected - handling column removal...")
                # Get table structure
                inspector = db.inspect(db.engine)
                columns = inspector.get_columns('access_log')
                pks = inspector.get_pk_constraint('access_log')
                
                if 'user_agent' not in [c['name'] for c in columns]:
                    print("ⓘ Column user_agent does not exist (already removed)")
                    return True
                
                # Get all existing data
                existing_logs = db.session.query(AccessLog).all()
                
                # Drop old table
                AccessLog.__table__.drop(db.engine)
                print("  - Dropped old table")
                
                # Recreate with new schema (user_agent field removed from model)
                AccessLog.__table__.create(db.engine)
                print("  - Created new table without user_agent column")
                
                # Re-insert data
                for log in existing_logs:
                    log.user_agent = None  # Clear to avoid the column
                    db.session.add(log)
                
                db.session.commit()
                print("✓ Migration completed successfully!")
                print(f"  - Re-inserted {len(existing_logs)} log entries")
                return True
    
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*70)
    print("ACCESS LOG DATA REDUNDANCY REMOVAL MIGRATION")
    print("="*70)
    print("\nChanges:")
    print("  • Remove unused user_agent column (512 bytes per entry)")
    print("  • Reduces database storage size")
    print("  • Improves query performance")
    print("\n" + "="*70 + "\n")
    
    success = run_migration()
    
    print("\n" + "="*70)
    if success:
        print("✓ Migration completed!")
        print("  Note: Restart the Flask application to load the updated schema")
    else:
        print("✗ Migration failed!")
    print("="*70 + "\n")
    
    exit(0 if success else 1)
