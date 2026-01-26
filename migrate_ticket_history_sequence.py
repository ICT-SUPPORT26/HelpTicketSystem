#!/usr/bin/env python
"""Migration script to fix ticket_history id sequence in PostgreSQL"""

from app import app
from models import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Create sequence if it doesn't exist
            db.session.execute(text("CREATE SEQUENCE IF NOT EXISTS ticket_history_id_seq"))

            # Set the default for id column
            db.session.execute(text("ALTER TABLE ticket_history ALTER COLUMN id SET DEFAULT nextval('ticket_history_id_seq')"))

            # Set the sequence to the current max id + 1
            db.session.execute(text("SELECT setval('ticket_history_id_seq', (SELECT COALESCE(MAX(id), 1) FROM ticket_history))"))

            db.session.commit()
            print('✓ Successfully fixed ticket_history id sequence')

        except Exception as e:
            print(f'✗ Error: {e}')
            db.session.rollback()
            return False

    return True

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)