#!/usr/bin/env python
"""
Migration script to create the access_log table.

This creates the table if it doesn't exist, with all necessary columns and indexes.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("\n" + "="*70)
    print("ACCESS LOG TABLE CREATION MIGRATION")
    print("="*70 + "\n")
    
    try:
        from app import db, app
        from models import AccessLog
        
        with app.app_context():
            # Check if table already exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            if 'access_log' in inspector.get_table_names():
                print("✓ access_log table already exists")
                
                # Check columns
                columns = [c['name'] for c in inspector.get_columns('access_log')]
                print(f"  Columns: {', '.join(columns)}")
                
                # Check indexes
                indexes = inspector.get_indexes('access_log')
                print(f"  Indexes: {len(indexes)} total")
                
                return True
            
            print("Creating access_log table...")
            
            # Create the table
            AccessLog.__table__.create(db.engine, checkfirst=True)
            
            print("✓ access_log table created successfully")
            
            # Verify indexes
            inspector = inspect(db.engine)
            indexes = inspector.get_indexes('access_log')
            
            print(f"\nTable Details:")
            print(f"  Columns created:")
            for col in inspector.get_columns('access_log'):
                print(f"    - {col['name']}: {col['type']}")
            
            print(f"\n  Indexes created: {len(indexes)}")
            for idx in indexes:
                print(f"    - {idx['name']}: {', '.join(idx['column_names'])}")
            
            print("\n✓ Migration completed successfully!")
            print("\nAccess logging is now ready to use.")
            print("Restart your Flask application to enable access logging.")
            
            return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    print("\n" + "="*70 + "\n")
    exit(0 if success else 1)
