from app import app
from utils import send_intern_approval_confirmation_email
from types import SimpleNamespace

with app.app_context():
    user = SimpleNamespace(full_name='Test Intern', username='testintern', email='your_test_recipient@example.com', role='intern')
    approver = SimpleNamespace(full_name='Admin User')
    ok = send_intern_approval_confirmation_email(user, approver)
    print('send_intern_approval_confirmation_email returned:', ok)
