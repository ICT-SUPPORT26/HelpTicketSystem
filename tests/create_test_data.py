
from app import app, db
from models import User, Ticket, Category, Comment
from datetime import datetime, timedelta
import random

def create_test_data():
    with app.app_context():
        # Get existing users and categories
        admin = User.query.filter_by(username='215030').first()
        intern = User.query.filter_by(username='dctraining').first()
        
        # Get categories
        categories = Category.query.all()
        
        if not admin or not intern or not categories:
            print("Missing required data (admin, intern, or categories)")
            return
        
        # Create some test users if they don't exist
        test_users = []
        for i, name in enumerate(['John Doe', 'Jane Smith', 'Bob Wilson'], 1):
            user = User.query.filter_by(username=f'user{i}').first()
            if not user:
                from werkzeug.security import generate_password_hash
                user = User(
                    username=f'user{i}',
                    email=f'user{i}@company.com',
                    password_hash=generate_password_hash('password'),
                    role='user',
                    full_name=name,
                    is_verified=True,
                    is_active=True
                )
                db.session.add(user)
            test_users.append(user)
        
        db.session.commit()
        
        # Create test tickets with various statuses and dates
        locations = [
            'SWA - LSHR - Hall 1',
            'SWA - LSHR - Hall 2', 
            'SWA - USHR - Hall 4',
            'UHS - Staff clinic',
            'UHS - Student clinic',
            'Confucius - Block A',
            'Confucius - Library'
        ]
        
        descriptions = [
            'Computer not starting up properly',
            'Printer not working - paper jam issue',
            'Internet connection very slow',
            'Email not receiving messages',
            'Software installation needed',
            'Password reset required',
            'Network connectivity issues',
            'Hardware replacement needed'
        ]
        
        priorities = ['low', 'medium', 'high', 'urgent']
        statuses = ['open', 'in_progress', 'resolved', 'closed']
        
        # Create tickets over the last 30 days
        for i in range(20):  # Create 20 test tickets
            # Random date within last 30 days
            days_ago = random.randint(0, 30)
            created_date = datetime.utcnow() - timedelta(days=days_ago)
            
            ticket = Ticket(
                location=random.choice(locations),
                description=random.choice(descriptions),
                priority=random.choice(priorities),
                status=random.choice(statuses),
                created_by_id=random.choice(test_users).id,
                category_id=random.choice(categories).id,
                created_at=created_date,
                updated_at=created_date + timedelta(hours=random.randint(1, 48))
            )
            
            # If ticket is resolved or closed, set closed_at
            if ticket.status in ['resolved', 'closed']:
                ticket.closed_at = ticket.updated_at
                ticket.closed_by_id = admin.id
            
            # Assign some tickets to intern
            if random.choice([True, False]):
                ticket.assignees.append(intern)
                if ticket.status == 'open':
                    ticket.status = 'in_progress'
            
            db.session.add(ticket)
        
        db.session.commit()
        print(f"Created {20} test tickets successfully!")
        
        # Verify tickets were created
        total_tickets = Ticket.query.count()
        print(f"Total tickets in database: {total_tickets}")

if __name__ == '__main__':
    create_test_data()
