"""Flask CLI commands for testing and debugging."""

import click
from flask.cli import with_appcontext
from sms_service import send_sms, _normalize_phone
import os


@click.group()
def cli():
    """SMS testing and diagnostic commands."""
    pass


@cli.command('test-sms')
@click.option('--phone', prompt='Phone number (e.g., 0712345678)', help='Recipient phone number')
@click.option('--message', prompt='Message text', default='Test SMS from HelpTicketSystem', help='SMS message')
@with_appcontext
def test_sms_cmd(phone, message):
    """Test SMS sending with given phone and message."""
    click.echo()
    click.echo("=" * 70)
    click.echo("SMS TEST")
    click.echo("=" * 70)
    click.echo()
    
    # Check environment
    username = os.environ.get("MOVESMS_USERNAME")
    apikey = os.environ.get("MOVESMS_APIKEY")
    
    if not username or not apikey:
        click.secho("❌ ERROR: MoveSMS credentials not configured", fg='red', bold=True)
        click.echo()
        click.echo("Set these environment variables:")
        click.echo("  $env:MOVESMS_USERNAME = 'your_username'")
        click.echo("  $env:MOVESMS_APIKEY = 'your_api_key'")
        click.echo()
        click.echo("Or copy .env.example to .env and fill in your credentials")
        return
    
    # Normalize phone
    click.echo(f"📱 Input phone: {phone}")
    normalized = _normalize_phone(phone)
    
    if not normalized:
        click.secho(f"❌ Invalid phone format: {phone}", fg='red')
        click.echo()
        click.echo("Accepted formats:")
        click.echo("  - 0712345678 (local Kenya)")
        click.echo("  - +254712345678 (international)")
        click.echo("  - 254712345678 (international without +)")
        click.echo("  - 712345678 (short form)")
        return
    
    click.echo(f"✓ Normalized: {normalized}")
    click.echo(f"📝 Message: {message!r}")
    click.echo(f"👤 Sender: {os.environ.get('MOVESMS_SENDER_ID', 'HELPDESK')}")
    click.echo()
    
    # Send SMS
    click.echo("📤 Sending SMS...")
    result = send_sms(phone, message)
    
    click.echo()
    if result:
        click.secho("✓ SMS sent successfully!", fg='green', bold=True)
        click.echo()
        click.echo("Check MoveSMS dashboard to confirm delivery")
    else:
        click.secho("❌ SMS send failed", fg='red', bold=True)
        click.echo()
        click.echo("Possible causes:")
        click.echo("  1. MoveSMS credentials are incorrect")
        click.echo("  2. API endpoint is unreachable")
        click.echo("  3. Phone number is invalid")
        click.echo("  4. Message is too long")
        click.echo()
        click.echo("Check application logs for detailed error messages")
    
    click.echo()


@cli.command('check-sms-config')
@with_appcontext
def check_sms_config():
    """Check SMS configuration status."""
    click.echo()
    click.echo("=" * 70)
    click.echo("SMS CONFIGURATION CHECK")
    click.echo("=" * 70)
    click.echo()
    
    username = os.environ.get("MOVESMS_USERNAME")
    apikey = os.environ.get("MOVESMS_APIKEY")
    sender_id = os.environ.get("MOVESMS_SENDER_ID", "HELPDESK")
    base_url = os.environ.get("MOVESMS_BASE_URL", "https://sms.movesms.co.ke/api/compose")
    
    click.echo("Configuration Variables:")
    click.echo(f"  MOVESMS_USERNAME:  {('✓ SET' if username else '✗ NOT SET'):<15} {username[:20] + '...' if username and len(username) > 20 else username or ''}")
    click.echo(f"  MOVESMS_APIKEY:    {('✓ SET' if apikey else '✗ NOT SET'):<15} {'***' if apikey else 'NOT SET'}")
    click.echo(f"  MOVESMS_SENDER_ID: {('✓ SET' if sender_id else 'DEFAULT'):<15} {sender_id}")
    click.echo(f"  MOVESMS_BASE_URL:  {'✓ SET':<15} {base_url}")
    click.echo()
    
    if not username or not apikey:
        click.secho("❌ SMS is NOT configured - no SMS will be sent", fg='red', bold=True)
        click.echo()
        click.echo("To enable SMS:")
        click.echo()
        click.echo("  1. Copy .env.example to .env")
        click.echo("  2. Fill in your MoveSMS credentials")
        click.echo("  3. Restart the application")
        click.echo()
        click.echo("Or set environment variables:")
        click.echo("  PowerShell:")
        click.echo("    $env:MOVESMS_USERNAME = 'your_username'")
        click.echo("    $env:MOVESMS_APIKEY = 'your_api_key'")
        click.echo()
    else:
        click.secho("✓ SMS is configured", fg='green', bold=True)
        click.echo()
        click.echo("Run 'flask test-sms' to send a test message")
    
    click.echo()


if __name__ == '__main__':
    cli()
