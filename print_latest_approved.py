from app import app, db
from models import User

with app.app_context():
    u = User.query.filter(User.role=='intern', User.is_approved==True, User.approved_at!=None).order_by(User.approved_at.desc()).first()
    if not u:
        print('No approved interns found')
    else:
        print('Latest approved intern:')
        print('id:', u.id)
        print('full_name:', u.full_name)
        print('email:', u.email)
        print('approved_at:', u.approved_at)
