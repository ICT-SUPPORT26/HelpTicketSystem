#!/usr/bin/env python
"""Manual SMS test - edit PHONE_NUMBER before running."""
import os
from dotenv import load_dotenv
load_dotenv()

# ===== EDIT THIS =====
PHONE_NUMBER = "+2547XXXXXXXX"  # Replace with actual phone number
TEST_MESSAGE = "Test SMS from HelpTicket system"
# ====================

print(f"Testing SMS to: {PHONE_NUMBER}")
print(f"Message: {TEST_MESSAGE}")

if "XXXXXXXX" in PHONE_NUMBER:
    print("\n✗ ERROR: Replace XXXXXXXX with actual phone number!")
    print("Format: +2547XXXXXXXX (Kenya) or 07XXXXXXXX")
    exit(1)

try:
    from app import app
    from sms_service import send_sms
    
    with app.app_context():
        print("\nSending SMS...")
        result = send_sms(PHONE_NUMBER, TEST_MESSAGE, provider="textbelt")
        
        if result:
            print("✓ SMS sent successfully!")
        else:
            print("✗ SMS send returned False - check logs above")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
