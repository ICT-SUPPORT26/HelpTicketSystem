#!/usr/bin/env python
"""Test script for report upload functionality"""

from app import app
from models import db, User, ReportFile
from werkzeug.security import generate_password_hash
import os

def test_report_upload():
    with app.app_context():
        try:
            # Create a test user if it doesn't exist
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash=generate_password_hash('password'),
                    role='intern'
                )
                db.session.add(test_user)
                db.session.commit()
                print('✓ Created test user')
            else:
                print('✓ Test user already exists')
            
            # Ensure upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Create a test file
            test_file_path = os.path.join(app.config['UPLOAD_FOLDER'], '20250101_000000_test.txt')
            with open(test_file_path, 'w') as f:
                f.write('Test report content for verification')
            
            file_size = os.path.getsize(test_file_path)
            print(f'✓ Created test file: {test_file_path} ({file_size} bytes)')
            
            # Create report record
            report = ReportFile(
                filename='20250101_000000_test.txt',
                original_filename='test.txt',
                file_size=file_size,
                content_type='text/plain',
                file_type='text',
                category='IT',
                uploaded_by_id=test_user.id
            )
            db.session.add(report)
            db.session.commit()
            
            print(f'✓ Report created in database with ID: {report.id}')
            
            # Verify retrieval
            retrieved = ReportFile.query.get(report.id)
            if retrieved:
                print(f'✓ Report retrieved successfully')
                print(f'  - Filename: {retrieved.original_filename}')
                print(f'  - Type: {retrieved.file_type}')
                print(f'  - Size: {retrieved.file_size} bytes')
                print(f'  - Uploaded by: {retrieved.uploaded_by.username}')
            
            # Check report count
            total_reports = ReportFile.query.count()
            print(f'✓ Total reports in database: {total_reports}')
            
            print('\n✅ Upload functionality test PASSED')
            return True
            
        except Exception as e:
            print(f'❌ Error: {str(e)}')
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_report_upload()
    exit(0 if success else 1)
