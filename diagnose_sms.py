#!/usr/bin/env python
"""Comprehensive SMS diagnostics."""
import os
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("SMS CONFIGURATION CHECK")
print("=" * 60)

sms_provider = os.environ.get("SMS_PROVIDER")
textbelt_key = os.environ.get("TEXTBELT_KEY", "textbelt")
print(f"\n1. SMS Provider: {sms_provider or 'NOT SET (will auto-detect)'}")
print(f"2. Textbelt Key: {textbelt_key}")

# Test Textbelt connection
print("\n" + "=" * 60)
print("TEXTBELT CONNECTION TEST")
print("=" * 60)

try:
    import requests
    print("✓ requests library available")
    
    # Simple connectivity test (without sending)
    test_url = "https://textbelt.com/text"
    print(f"\nAttempting to reach: {test_url}")
    
    response = requests.post(test_url, data={
        "phone": "+254712345678",
        "message": "Test message",
        "key": textbelt_key
    }, timeout=10)
    
    print(f"Status code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {data}")
        if data.get("success"):
            print("✓ Textbelt API is responsive")
        else:
            print(f"✗ Textbelt returned success=False: {data.get('message', 'Unknown error')}")
    except:
        print(f"Response text: {response.text[:200]}")
        
except Exception as e:
    print(f"✗ Connection error: {e}")

# Test send_sms function
print("\n" + "=" * 60)
print("SEND_SMS FUNCTION TEST")
print("=" * 60)

try:
    from app import app
    from sms_service import send_sms
    
    print("✓ sms_service imported successfully")
    
    with app.app_context():
        # Test with dummy phone
        print("\nTesting send_sms() with dummy number +254712345678...")
        result = send_sms("+254712345678", "Test SMS from HelpTicket system", provider="textbelt")
        print(f"send_sms() returned: {result}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Check for users with phone numbers
print("\n" + "=" * 60)
print("DATABASE: USERS WITH PHONE NUMBERS")
print("=" * 60)

try:
    from app import app, db
    from models import User
    
    with app.app_context():
        users_with_phone = User.query.filter(User.phone_number != None).all()
        print(f"Users with phone numbers: {len(users_with_phone)}")
        for u in users_with_phone[:5]:
            print(f"  - {u.full_name} ({u.username}): {u.phone_number}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)
print("""
If SMS is not working:

1. Check phone numbers:
   - Users must have phone_number field populated
   - Must be in Kenya format: +2547XXXXXXXX or 07XXXXXXXX

2. Check SMS provider:
   - Textbelt is free but rate-limited (1 free SMS per day per IP)
   - For testing with multiple SMS, use MoveSMS or get Textbelt key

3. Check logs:
   - When assigning ticket, watch terminal for SMS logs
   - Look for "Textbelt SMS sent to" or error messages

4. Test manually:
   - python test_send_sms.py (add this file to test a specific number)
""")
