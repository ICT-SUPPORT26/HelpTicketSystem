from app import app, db
from models import User

def verify_existing_users():
    with app.app_context():
        # Show all users and their verification status
        all_users = User.query.all()
        print(f"Total users: {len(all_users)}")
        for user in all_users:
            print(f"User: {user.username} ({user.full_name}) - Role: {user.role} - Verified: {user.is_verified} - Active: {user.is_active} - Approved: {user.is_approved}")

        # Update ALL users that are not verified
        users_to_verify = User.query.filter(User.is_verified == False).all()

        for user in users_to_verify:
            user.is_verified = True
            user.verification_token = None
            print(f"Verified user: {user.username} ({user.full_name})")

        if users_to_verify:
            db.session.commit()
            print(f"Updated {len(users_to_verify)} users to verified status")
        else:
            print("No unverified users found")

if __name__ == '__main__':
    verify_existing_users()