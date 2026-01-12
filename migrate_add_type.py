#!/usr/bin/env python
"""Migration script to add `type` column to report_file and populate values.

This script is safe to run multiple times. It will:
 - add the `type` column (VARCHAR(50)) if it doesn't exist
 - populate `type` for existing rows using `get_file_category(original_filename, content_type)`
 - leave the column nullable (models expect a value; upload code sets it on new rows)

Run with: `python migrate_add_type.py`
"""
from app import app
from models import db, ReportFile
from sqlalchemy import text
import traceback

def get_file_category(filename, content_type):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    content_type_lower = (content_type or '').lower()

    if ext in ['pdf'] or 'pdf' in content_type_lower:
        return 'pdf'
    elif ext in ['csv'] or 'csv' in content_type_lower:
        return 'csv'
    elif ext in ['xlsx', 'xls'] or 'spreadsheet' in content_type_lower or 'excel' in content_type_lower:
        return 'excel'
    elif ext in ['docx', 'doc'] or 'word' in content_type_lower:
        return 'word'
    elif ext in ['pptx', 'ppt'] or 'presentation' in content_type_lower:
        return 'ppt'
    elif ext in ['txt'] or 'text' in content_type_lower:
        return 'text'
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp'] or 'image' in content_type_lower:
        return 'image'
    else:
        return 'other'

def migrate():
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='report_file' AND COLUMN_NAME='type'"
            ))

            if result.fetchone():
                print('✓ `type` column already exists on report_file')
            else:
                print('Adding `type` column to report_file...')
                db.session.execute(text("ALTER TABLE report_file ADD COLUMN `type` VARCHAR(50) NULL"))
                db.session.commit()
                print('✓ Added `type` column')

            # Populate `type` for rows where NULL or empty
            reports = ReportFile.query.filter((ReportFile.file_type == None) | (ReportFile.file_type == '')).all()
            if not reports:
                print('✓ No existing report rows require population')
                return True

            print(f'Updating {len(reports)} report rows to set `type`...')
            for r in reports:
                try:
                    inferred = get_file_category(r.original_filename or r.filename or '', r.content_type)
                    r.file_type = inferred
                except Exception:
                    r.file_type = 'other'

            db.session.commit()
            print('✓ Populated `type` for existing rows')

        except Exception as e:
            print('✗ Migration failed:')
            traceback.print_exc()
            db.session.rollback()
            return False

    return True

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
