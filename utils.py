from datetime import datetime, timedelta
from flask import url_for
from sqlalchemy import func
from flask import current_app
from flask_mail import Message
from extensions import mail
from models import Ticket, User, Comment


def send_notification_email(ticket, event_type):
    """Send notification email for ticket events"""
    try:
        recipients = []
        subject = ""
        template = ""

        if event_type == 'new_ticket':
            if ticket.assignees:
                recipients.extend([assignee.email for assignee in ticket.assignees])
            subject = f"New Ticket Assigned: #{ticket.id} - {ticket.location}"
            template = f"""
            A new ticket has been assigned to you:

            Ticket ID: #{ticket.id}
            Location: {ticket.location}
            Priority: {ticket.priority}
            Created by: {ticket.creator.full_name if ticket.creator else 'Unknown'}

            Please log in to the helpdesk system to view details.
            """

        elif event_type == 'ticket_updated':
            if ticket.creator:
                recipients.append(ticket.creator.email)
            for assignee in ticket.assignees:
                if assignee.email not in recipients:
                    recipients.append(assignee.email)
            subject = f"Ticket Updated: #{ticket.id} - {ticket.location}"
            template = f"""
            A ticket has been updated:

            Ticket ID: #{ticket.id}
            Location: {ticket.location}
            Status: {ticket.status}
            Priority: {ticket.priority}

            Please log in to the helpdesk system to view details.
            """

        elif event_type == 'new_comment':
            if ticket.creator:
                recipients.append(ticket.creator.email)
            for assignee in ticket.assignees:
                if assignee.email not in recipients:
                    recipients.append(assignee.email)
            subject = f"New Comment on Ticket: #{ticket.id}"
            template = f"""
            A new comment has been added to your ticket:

            Ticket ID: #{ticket.id}
            Location: {ticket.location}

            Please log in to the helpdesk system to view the comment.
            """

        if recipients and current_app.config.get('MAIL_USERNAME'):
            msg = Message(subject, recipients=recipients)
            msg.body = template
            mail.send(msg)

    except Exception as e:
        print(f"Error sending email: {e}")

def get_dashboard_stats(user):
    """Get dashboard statistics based on user role"""
    from models import Ticket, User

    stats = {}

    if user.role == 'admin':
        stats['total_tickets'] = Ticket.query.count()
        stats['open_tickets'] = Ticket.query.filter_by(status='open').count()
        stats['in_progress_tickets'] = Ticket.query.filter_by(status='in_progress').count()
        stats['resolved_tickets'] = Ticket.query.filter_by(status='resolved').count()
        stats['closed_tickets'] = Ticket.query.filter_by(status='closed').count()
        stats['total_users'] = User.query.count()

        # Urgent tickets
        stats['urgent_tickets'] = Ticket.query.filter_by(priority='urgent').filter(
            Ticket.status.in_(['open', 'in_progress'])
        ).count()

    elif user.role == 'intern':
        stats['assigned_tickets'] = Ticket.query.filter(Ticket.assignees.any(id=user.id)).count()
        stats['my_open_tickets'] = Ticket.query.filter(Ticket.assignees.any(id=user.id), Ticket.status == 'open').count()
        stats['my_in_progress'] = Ticket.query.filter(Ticket.assignees.any(id=user.id), Ticket.status == 'in_progress').count()
        stats['my_resolved'] = Ticket.query.filter(Ticket.assignees.any(id=user.id), Ticket.status == 'resolved').count()
        stats['my_closed'] = Ticket.query.filter(Ticket.assignees.any(id=user.id), Ticket.status == 'closed').count()

    else:  # user
        stats['my_tickets'] = Ticket.query.filter_by(created_by_id=user.id).count()
        stats['my_open'] = Ticket.query.filter_by(created_by_id=user.id, status='open').count()
        stats['my_in_progress'] = Ticket.query.filter_by(created_by_id=user.id, status='in_progress').count()
        stats['my_resolved'] = Ticket.query.filter_by(created_by_id=user.id, status='resolved').count()
        stats['my_closed'] = Ticket.query.filter_by(created_by_id=user.id, status='closed').count()

    return stats

def get_priority_badge_class(priority):
    """Get Bootstrap badge class for priority"""
    classes = {
        'low': 'bg-secondary',
        'medium': 'bg-warning',
        'high': 'bg-danger',
        'urgent': 'bg-danger'
    }
    return classes.get(priority, 'bg-secondary')

def get_status_badge_class(status):
    """Get Bootstrap badge class for status"""
    classes = {
        'open': 'bg-primary',
        'in_progress': 'bg-warning',
        'escalated': 'bg-danger',
        'resolved': 'bg-success',
        'closed': 'bg-secondary'
    }
    return classes.get(status, 'bg-secondary')

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return 'N/A'
    return dt.strftime('%Y-%m-%d %H:%M')

def time_ago(dt):
    """Get human-readable time difference"""
    if not dt:
        return 'N/A'

    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

# Template filters
def nl2br(value):
    """Convert newlines to HTML line breaks"""
    if not value:
        return value
    return value.replace('\n', '<br>')

def register_template_filters(app):
    app.jinja_env.filters['priority_badge'] = get_priority_badge_class
    app.jinja_env.filters['status_badge'] = get_status_badge_class
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['nl2br'] = nl2br

# Register filters
from app import app as flask_app
register_template_filters(flask_app)