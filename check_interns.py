from app import app, db
from models import User

with app.app_context():
    interns = User.query.filter_by(role='intern').all()
    print(f"Total interns: {len(interns)}")
    for intern in interns:
        print(f"  ID: {intern.id}, Name: {intern.full_name}, Approved: {intern.is_approved}, Verified: {intern.is_verified}, Active: {intern.is_active}")
    
    pending = User.query.filter_by(is_approved=False, is_verified=True, role='intern').all()
    print(f"\nPending approval (is_approved=False, is_verified=True): {len(pending)}")
    for p in pending:
        print(f"  {p.full_name}")
    
    unverified = User.query.filter_by(is_approved=False, is_verified=False, role='intern').all()
    print(f"\nUnverified interns (is_approved=False, is_verified=False): {len(unverified)}")
    for u in unverified:
        print(f"  {u.full_name}")
