from app import app, db
from models import User
from werkzeug.security import generate_password_hash


def test_logout_removes_cookies(client):
    # Ensure admin exists
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@local', full_name='Admin', password_hash=generate_password_hash('admin123'), role='admin', is_verified=True, is_active=True, is_approved=True)
            db.session.add(admin)
            db.session.commit()

    # Login with remember
    rv = client.post('/login', data={'username': 'admin', 'password': 'admin123', 'remember_me': 'y'}, follow_redirects=False)
    assert rv.status_code in (302, 303)

    # Ensure remember cookie exists in client cookie jar
    cookie_names = [c.name for domain in client.cookie_jar._cookies.values() for path in domain.values() for c in path.values()]
    assert any('remember' in name for name in cookie_names), f"Remember cookie not set: {cookie_names}"

    # Logout
    rv2 = client.get('/logout', follow_redirects=False)
    assert rv2.status_code in (302, 303)

    # After logout, ensure client cookie jar no longer has a remember cookie
    cookie_names_after = [c.name for domain in client.cookie_jar._cookies.values() for path in domain.values() for c in path.values()]
    assert not any('remember' in name for name in cookie_names_after), f"Remember cookie still present: {cookie_names_after}"

    # Access protected page -> should redirect to login/index
    rv3 = client.get('/dashboard', follow_redirects=False)
    assert rv3.status_code in (302, 303)
    assert '/login' in (rv3.headers.get('Location') or '') or rv3.headers.get('Location') == '/' or '/index' in (rv3.headers.get('Location') or '')
