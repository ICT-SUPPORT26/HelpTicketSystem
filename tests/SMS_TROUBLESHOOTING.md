# SMS Troubleshooting Guide

## Quick Diagnosis

Run this first:
```bash
python diagnose_sms.py
```

This will check:
- ✓ SMS provider configured
- ✓ Textbelt connectivity
- ✓ Users with phone numbers in DB
- ✓ send_sms() function working

## Most Common Issues

### 1. **Phone Numbers Not Set**
Users need phone numbers to receive SMS.

**Check if users have phone numbers:**
```bash
python diagnose_sms.py
```
Look for: "Users with phone numbers: X"

**Add phone number to a user:**
- Go to Admin > User Management
- Find the user
- Click "Edit" and add phone number in format: +2547XXXXXXXX or 07XXXXXXXX

### 2. **Textbelt Free Rate Limit**
Textbelt free key allows **1 SMS per day per IP**.

**Solutions:**
- Wait 24 hours and try again, OR
- Get a paid Textbelt key from https://textbelt.com, OR
- Switch to MoveSMS by setting in `.env`:
  ```
  SMS_PROVIDER=movesms
  MOVESMS_USERNAME=your_username
  MOVESMS_APIKEY=your_api_key
  ```

### 3. **Invalid Phone Number Format**
SMS only works with Kenya phone numbers.

**Valid formats:**
- ✓ +2547XXXXXXXX (international)
- ✓ 07XXXXXXXX (Kenya domestic)

**Invalid formats:**
- ✗ 2547XXXXXXXX (missing +)
- ✗ 7XXXXXXXX (too short)
- ✗ +1234567890 (non-Kenya)

## Manual Testing

1. **Test SMS sending directly:**
   ```bash
   # Edit test_send_sms.py - replace PHONE_NUMBER
   python test_send_sms.py
   ```

2. **Watch logs during ticket assignment:**
   - Assign a ticket to a user with phone number
   - Watch the Flask console for:
     - "Textbelt SMS sent to +254..."  (success)
     - or error messages

3. **Check Textbelt status:**
   - Go to https://textbelt.com/status
   - Verify API is up

## Verify SMS is Being Called

When you assign a ticket, check if SMS code is even reached:

1. Go to ticket detail page
2. Click "Update Ticket"
3. Change assignee(s)
4. Click Submit
5. Watch terminal for:
   - "SMS notification sent to 1 assignee" (flash message shown)
   - "Textbelt SMS sent to +254..." (in logs)
   - or error message

## Next Steps

1. Run `python diagnose_sms.py`
2. Share the output
3. We can fix the specific issue

Common fixes:
- Add phone numbers to users
- Use paid Textbelt key or MoveSMS
- Verify phone number format is correct
