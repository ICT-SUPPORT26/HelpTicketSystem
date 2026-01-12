#!/usr/bin/env python
"""Migration script to add category column to report_file table"""

from app import app
from models import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='report_file' AND COLUMN_NAME='category'"
            ))
            
            if result.fetchone():
                print('✓ category column already exists')
                return
            
            # Add column if it doesn't exist
            db.session.execute(text('ALTER TABLE report_file ADD COLUMN category VARCHAR(100) NULL'))
            db.session.commit()
            print('✓ Successfully added category column to report_file table')
            
        except Exception as e:
            print(f'✗ Error: {e}')
            db.session.rollback()
            return False
        
    return True

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
