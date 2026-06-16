from app import app
from models import User

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    print('admin exists?', bool(admin))

with app.test_client() as c:
    # Login as admin (existing admin user) — adjust username/password as needed
    resp = c.post('/login', data={'username': 'admin', 'password': 'admin123'})
    print('\nPOST /login status:', resp.status_code)
    print('Set-Cookie headers after login:')
    for h in resp.headers.getlist('Set-Cookie'):
        print(' -', h)

    # Show cookie jar
    try:
        cookies = []
        for domain, path_dict in c.cookie_jar._cookies.items():
            for path, cookies_map in path_dict.items():
                for name, cookie in cookies_map.items():
                    cookies.append((name, cookie.value))
        print('Cookies in jar:', cookies)
    except Exception as e:
        print('Cookie jar read failed:', e)

    # Logout
    resp2 = c.get('/logout')
    print('\nGET /logout status:', resp2.status_code)
    print('Set-Cookie headers after logout:')
    for h in resp2.headers.getlist('Set-Cookie'):
        print(' -', h)

    # Try accessing dashboard (should redirect to index/login)
    resp3 = c.get('/dashboard', follow_redirects=False)
    print('\nGET /dashboard status:', resp3.status_code)
    print('dashboard redirect location:', resp3.headers.get('Location'))
