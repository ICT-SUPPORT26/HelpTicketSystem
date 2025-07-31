
from app import app, db
from models import User, Ticket, Category
from datetime import datetime, timedelta
import pytz

def create_test_data():
    """Create test data for reports"""
    with app.app_context():
        # Create a test category if it doesn't exist
        category = Category.query.filter_by(name='Test Category').first()
        if not category:
            category = Category(name='Test Category', description='Test category for reports')
            db.session.add(category)
            db.session.flush()
        
        # Get admin user
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("No admin user found. Please create one first.")
            return
        
        # Create some test tickets with different statuses
        nairobi_tz = pytz.timezone('Africa/Nairobi')
        now = datetime.now(nairobi_tz)
        
        test_tickets = [
            {
                'location': 'Test Location 1',
                'description': 'Test ticket 1 - Open',
                'status': 'open',
                'priority': 'medium',
                'created_at': now - timedelta(days=2),
                'updated_at': now - timedelta(days=2)
            },
            {
                'location': 'Test Location 2',
                'description': 'Test ticket 2 - In Progress',
                'status': 'in_progress',
                'priority': 'high',
                'created_at': now - timedelta(days=1),
                'updated_at': now - timedelta(hours=2)
            },
            {
                'location': 'Test Location 3',
                'description': 'Test ticket 3 - Resolved',
                'status': 'resolved',
                'priority': 'low',
                'created_at': now - timedelta(days=3),
                'updated_at': now - timedelta(hours=6),
                'closed_at': now - timedelta(hours=6)
            },
            {
                'location': 'Test Location 4',
                'description': 'Test ticket 4 - Closed',
                'status': 'closed',
                'priority': 'urgent',
                'created_at': now - timedelta(days=4),
                'updated_at': now - timedelta(hours=12),
                'closed_at': now - timedelta(hours=12)
            }
        ]
        
        for ticket_data in test_tickets:
            # Check if ticket already exists
            existing = Ticket.query.filter_by(description=ticket_data['description']).first()
            if not existing:
                ticket = Ticket(
                    location=ticket_data['location'],
                    description=ticket_data['description'],
                    status=ticket_data['status'],
                    priority=ticket_data['priority'],
                    created_by_id=admin.id,
                    category_id=category.id,
                    created_at=ticket_data['created_at'],
                    updated_at=ticket_data['updated_at'],
                    closed_at=ticket_data.get('closed_at'),
                    closed_by_id=admin.id if ticket_data.get('closed_at') else None
                )
                db.session.add(ticket)
                print(f"Created test ticket: {ticket_data['description']}")
        
        db.session.commit()
        print("Test data created successfully!")

if __name__ == "__main__":
    create_test_data()
