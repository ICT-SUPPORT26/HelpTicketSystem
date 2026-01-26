#!/usr/bin/env python
"""Migration script to alter boolean columns in user table to proper BOOLEAN type"""

from app import app
from models import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Alter is_active column to BOOLEAN
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN is_active TYPE BOOLEAN USING is_active::boolean'))
            print('✓ Altered is_active to BOOLEAN')

            # Alter is_verified column to BOOLEAN
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN is_verified TYPE BOOLEAN USING is_verified::boolean'))
            print('✓ Altered is_verified to BOOLEAN')

            # Alter is_approved column to BOOLEAN
            db.session.execute(text('ALTER TABLE "user" ALTER COLUMN is_approved TYPE BOOLEAN USING is_approved::boolean'))
            print('✓ Altered is_approved to BOOLEAN')

            db.session.commit()
            print('✓ Successfully altered all boolean columns in user table')

        except Exception as e:
            print(f'✗ Error: {e}')
            db.session.rollback()
            return False

    return True

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)