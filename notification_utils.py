from datetime import datetime, time
from models import Notification, NotificationSettings, User
from extensions import db
from utils import send_notification_email

class NotificationManager:
    @staticmethod
    def create_notification(user_id, ticket_id, notification_type, title, message):
        """Create a new notification for a user"""
        try:
            notification = Notification(
                user_id=user_id,
                ticket_id=ticket_id,
                type=notification_type,
                title=title,
                message=message,
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            return notification
        except Exception as e:
            print(f"Error creating notification: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def notify_new_ticket(ticket):
        """Send notifications for new tickets"""
        try:
            # Notify all admins about new unassigned tickets
            if not ticket.assignees:
                admins = User.query.filter_by(role='admin', is_active=True).all()
                for admin in admins:
                    NotificationManager.create_notification(
                        user_id=admin.id,
                        ticket_id=ticket.id,
                        notification_type='new_ticket',
                        title=f'New Unassigned Ticket: #{ticket.id}',
                        message=f'A new ticket has been created that needs assignment.\n\nLocation: {ticket.location}\nPriority: {ticket.priority}\nCreated by: {ticket.creator.full_name if ticket.creator else "Unknown"}'
                    )

            # Notify assignees
            for assignee in ticket.assignees:
                NotificationManager.create_notification(
                    user_id=assignee.id,
                    ticket_id=ticket.id,
                    notification_type='ticket_assigned',
                    title=f'New Ticket Assigned: #{ticket.id}',
                    message=f'A new ticket has been assigned to you.\n\nLocation: {ticket.location}\nPriority: {ticket.priority}\nCreated by: {ticket.creator.full_name if ticket.creator else "Unknown"}'
                )

            # Send email notifications if configured
            send_notification_email(ticket, 'new_ticket')

        except Exception as e:
            print(f"Error sending new ticket notifications: {e}")

    @staticmethod
    def notify_ticket_updated(ticket, updated_by):
        """Send notifications when ticket is updated"""
        try:
            # Notify ticket creator if different from updater
            if ticket.creator and ticket.creator.id != updated_by.id:
                NotificationManager.create_notification(
                    user_id=ticket.creator.id,
                    ticket_id=ticket.id,
                    notification_type='ticket_updated',
                    title=f'Ticket Updated: #{ticket.id}',
                    message=f'Your ticket has been updated by {updated_by.full_name}.\n\nLocation: {ticket.location}\nStatus: {ticket.status}\nPriority: {ticket.priority}'
                )

            # Notify assignees if different from updater
            for assignee in ticket.assignees:
                if assignee.id != updated_by.id:
                    NotificationManager.create_notification(
                        user_id=assignee.id,
                        ticket_id=ticket.id,
                        notification_type='ticket_updated',
                        title=f'Assigned Ticket Updated: #{ticket.id}',
                        message=f'A ticket assigned to you has been updated by {updated_by.full_name}.\n\nLocation: {ticket.location}\nStatus: {ticket.status}\nPriority: {ticket.priority}'
                    )

            # Send email notifications
            send_notification_email(ticket, 'ticket_updated')

        except Exception as e:
            print(f"Error sending ticket update notifications: {e}")

    @staticmethod
    def notify_new_comment(ticket, comment_author):
        """Send notifications for new comments"""
        try:
            # Notify ticket creator if different from comment author
            if ticket.creator and ticket.creator.id != comment_author.id:
                NotificationManager.create_notification(
                    user_id=ticket.creator.id,
                    ticket_id=ticket.id,
                    notification_type='new_comment',
                    title=f'New Comment on Ticket #{ticket.id}',
                    message=f'{comment_author.full_name} added a comment to your ticket.\n\nLocation: {ticket.location}'
                )

            # Notify assignees if different from comment author
            for assignee in ticket.assignees:
                if assignee.id != comment_author.id:
                    NotificationManager.create_notification(
                        user_id=assignee.id,
                        ticket_id=ticket.id,
                        notification_type='new_comment',
                        title=f'New Comment on Assigned Ticket #{ticket.id}',
                        message=f'{comment_author.full_name} added a comment to a ticket assigned to you.\n\nLocation: {ticket.location}'
                    )

            # Send email notifications
            send_notification_email(ticket, 'new_comment')

        except Exception as e:
            print(f"Error sending new comment notifications: {e}")

    @staticmethod
    def notify_ticket_closed(ticket, closed_by):
        """Send notifications when ticket is closed"""
        try:
            # Notify ticket creator if different from closer
            if ticket.creator and ticket.creator.id != closed_by.id:
                NotificationManager.create_notification(
                    user_id=ticket.creator.id,
                    ticket_id=ticket.id,
                    notification_type='ticket_closed',
                    title=f'Ticket Closed: #{ticket.id}',
                    message=f'Your ticket has been closed by {closed_by.full_name}.\n\nLocation: {ticket.location}'
                )

            # Notify assignees if different from closer
            for assignee in ticket.assignees:
                if assignee.id != closed_by.id:
                    NotificationManager.create_notification(
                        user_id=assignee.id,
                        ticket_id=ticket.id,
                        notification_type='ticket_closed',
                        title=f'Assigned Ticket Closed: #{ticket.id}',
                        message=f'A ticket assigned to you has been closed by {closed_by.full_name}.\n\nLocation: {ticket.location}'
                    )

        except Exception as e:
            print(f"Error sending ticket closed notifications: {e}")

    @staticmethod
    def get_user_notifications(user_id, limit=20):
        """Get notifications for a user"""
        try:
            notifications = Notification.query.filter_by(user_id=user_id).order_by(
                Notification.created_at.desc()
            ).limit(limit).all()
            return notifications
        except Exception as e:
            print(f"Error getting user notifications: {e}")
            return []

    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user"""
        try:
            count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
            print(f"DEBUG: Unread count calculation - User: {user_id}, Unread: {count}")

            # Debug: Show all notifications for this user
            all_notifications = Notification.query.filter_by(user_id=user_id).all()
            total_count = len(all_notifications)
            print(f"DEBUG: Total notifications: {total_count}")

            for notif in all_notifications:
                print(f"DEBUG: Notification {notif.id}: is_read={notif.is_read}, title='{notif.title}'")

            return count
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a notification as read"""
        try:
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            db.session.rollback()
            return False

    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all notifications as read for a user"""
        try:
            notifications = Notification.query.filter_by(user_id=user_id, is_read=False).all()
            count = len(notifications)
            for notification in notifications:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
            db.session.commit()
            return count
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            db.session.rollback()
            return 0

    @staticmethod
    def clear_all_notifications(user_id):
        """Clear all notifications for a user"""
        try:
            count = Notification.query.filter_by(user_id=user_id).count()
            Notification.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            return count
        except Exception as e:
            print(f"Error clearing notifications: {e}")
            db.session.rollback()
            return 0

    @staticmethod
    def notify_new_user_registration(user):
        """Send notifications to admins about new user registration"""
        try:
            admins = User.query.filter_by(role='admin', is_active=True).all()
            for admin in admins:
                NotificationManager.create_notification(
                    user_id=admin.id,
                    ticket_id=None,
                    notification_type='user_registered',
                    title=f'New User Registration: {user.full_name}',
                    message=f'A new {user.role} has registered and needs approval.\n\nName: {user.full_name}\nEmail: {user.email}\nUsername: {user.username}\nRole: {user.role.title()}\n\nPlease review and approve their account in the user management section.'
                )
        except Exception as e:
            print(f"Error sending user registration notifications: {e}")

    @staticmethod
    def notify_user_approved(user, approved_by):
        """Send notification to user when their account is approved"""
        try:
            NotificationManager.create_notification(
                user_id=user.id,
                ticket_id=None,
                notification_type='account_approved',
                title='Account Approved - Welcome to ICT Helpdesk!',
                message=f'Your account has been approved by {approved_by.full_name}.\n\nYou can now access the ICT Helpdesk system and start working with tickets.\n\nWelcome to the team!'
            )
        except Exception as e:
            print(f"Error sending user approval notification: {e}")