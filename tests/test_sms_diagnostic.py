#!/usr/bin/env python
"""Diagnostic script to test SMS sending configuration and functionality."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sms_service import send_sms, _normalize_phone

def check_environment():
    """Check if MoveSMS environment variables are configured."""
    print("=" * 60)
    print("SMS SERVICE DIAGNOSTIC")
    print("=" * 60)
    print()
    
    username = os.environ.get("MOVESMS_USERNAME")
    apikey = os.environ.get("MOVESMS_APIKEY")
    sender_id = os.environ.get("MOVESMS_SENDER_ID", "HELPDESK")
    base_url = os.environ.get("MOVESMS_BASE_URL", "https://sms.movesms.co.ke/api/compose")
    
    print("📋 Configuration Status:")
    print(f"  MOVESMS_USERNAME:  {'✓ SET' if username else '✗ NOT SET'}")
    print(f"  MOVESMS_APIKEY:    {'✓ SET' if apikey else '✗ NOT SET'}")
    print(f"  MOVESMS_SENDER_ID: {'✓ SET' if sender_id else '✗ DEFAULT'} (value: {sender_id})")
    print(f"  MOVESMS_BASE_URL:  {base_url}")
    print()
    
    if not username or not apikey:
        print("❌ SMS Configuration Incomplete")
        print()
        print("To enable SMS sending, set these environment variables:")
        print()
        print("  PowerShell:")
        print("    $env:MOVESMS_USERNAME = 'your_username'")
        print("    $env:MOVESMS_APIKEY = 'your_api_key'")
        print("    $env:MOVESMS_SENDER_ID = 'HELPDESK'  # optional, defaults to HELPDESK")
        print()
        print("  Command Prompt (cmd.exe):")
        print("    set MOVESMS_USERNAME=your_username")
        print("    set MOVESMS_APIKEY=your_api_key")
        print("    set MOVESMS_SENDER_ID=HELPDESK")
        print()
        print("  Or add to .env file (if using python-dotenv):")
        print("    MOVESMS_USERNAME=your_username")
        print("    MOVESMS_APIKEY=your_api_key")
        print("    MOVESMS_SENDER_ID=HELPDESK")
        print()
        return False
    return True

def test_phone_normalization():
    """Test phone number normalization."""
    print("🔍 Phone Normalization Tests:")
    print()
    
    test_cases = [
        ("0712345678", "254712345678"),
        ("+254712345678", "254712345678"),
        ("254712345678", "254712345678"),
        ("712345678", "254712345678"),
        ("invalid", None),
        (None, None),
    ]
    
    all_pass = True
    for phone, expected in test_cases:
        result = _normalize_phone(phone)
        status = "✓" if result == expected else "✗"
        all_pass = all_pass and (result == expected)
        print(f"  {status} _normalize_phone({phone!r}) = {result!r} (expected {expected!r})")
    
    print()
    return all_pass

def test_sms_send():
    """Test actual SMS sending."""
    print("📱 SMS Send Test:")
    print()
    
    # Test with a valid Kenyan phone number
    test_phone = "0712345678"  # This won't actually receive SMS without real credentials
    test_message = "Test SMS from HelpTicketSystem diagnostic"
    
    print(f"  Sending test SMS to: {test_phone}")
    print(f"  Message: {test_message!r}")
    print()
    
    result = send_sms(test_phone, test_message)
    
    if result:
        print("  ✓ SMS send returned: True (check MoveSMS dashboard to confirm delivery)")
    else:
        print("  ✗ SMS send returned: False")
        print("    - Check MOVESMS_USERNAME and MOVESMS_APIKEY are correct")
        print("    - Check internet connection")
        print("    - Check MoveSMS API endpoint is accessible")
        print("    - View application logs for detailed error messages")
    
    print()
    return result

if __name__ == "__main__":
    print()
    
    # Check environment
    env_ok = check_environment()
    
    if env_ok:
        # Test normalization
        norm_ok = test_phone_normalization()
        
        # Test SMS send
        print("-" * 60)
        send_ok = test_sms_send()
        
        print("=" * 60)
        if send_ok:
            print("✓ SMS Service appears to be working correctly")
        else:
            print("✗ SMS Service has issues - review logs above")
    
    print()
