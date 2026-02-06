#!/usr/bin/env python
"""Check mail configuration."""
import os
from dotenv import load_dotenv
load_dotenv()

mail_configured = bool(os.environ.get('MAIL_USERNAME') and os.environ.get('MAIL_PASSWORD'))
print(f'Mail configured: {mail_configured}')
print(f'Mail server: {os.environ.get("MAIL_SERVER", "smtp.gmail.com")}')
print(f'Mail username: {os.environ.get("MAIL_USERNAME", "NOT SET")}')
print(f'Mail password: {"SET" if os.environ.get("MAIL_PASSWORD") else "NOT SET"}')
print(f'Mail default sender: {os.environ.get("MAIL_DEFAULT_SENDER", "helpticketsystem@outlook.com")}')
