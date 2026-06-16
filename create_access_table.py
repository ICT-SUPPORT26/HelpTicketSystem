#!/usr/bin/env python
"""
Simple migration to create access_log table using Flask app context.
"""

def main():
    print("\n" + "="*70)
    print("ACCESS LOG TABLE INITIALIZATION")
    print("="*70 + "\n")
    
    try:
        from app import db, app
        from models import AccessLog
        from sqlalchemy import inspect
        
        with app.app_context():
            inspector = inspect(db.engine)
            
            if 'access_log' in inspector.get_table_names():
                print("✓ access_log table already exists\n")
                return True
            
            print("Creating access_log table...")
            AccessLog.__table__.create(db.engine)
            print("✓ access_log table created successfully\n")
            
            # Verify
            inspector = inspect(db.engine)
            if 'access_log' in inspector.get_table_names():
                print("Table Details:")
                for col in inspector.get_columns('access_log'):
                    print(f"  - {col['name']}: {col['type']}")
                print("\n✓ Migration completed successfully!")
                return True
            else:
                print("✗ Table not found after creation")
                return False
                
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    print("\n" + "="*70 + "\n")
    exit(0 if success else 1)
