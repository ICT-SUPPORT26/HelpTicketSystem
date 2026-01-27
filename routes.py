import os
from datetime import datetime, timedelta
from flask import render_template, flash, redirect, url_for, request, send_from_directory, abort, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc
from flask_mail import Message
import pytz
import uuid
from sqlalchemy.orm import joinedload
from flask_caching import Cache
#SMS service
from sms_service import send_sms

from app import app, db, mail
from models import User, Ticket, Comment, Attachment, Category, Notification, NotificationSettings, ReportFile
from forms import LoginForm, RegistrationForm, TicketForm, CommentForm, TicketUpdateForm, UserManagementForm, CategoryForm, AdminUserForm, NotificationSettingsForm, PasswordChangeForm, UserStatusForm
from utils import send_notification_email, get_dashboard_stats
from notification_utils import NotificationManager
from background_tasks import generate_report_data

# Initialize cache
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

@app.route('/')
def index():
    # Render login form (Flask-WTF) so a CSRF token is generated and stored in the session
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    return render_template('index.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Use Flask-WTF LoginForm (ensures CSRF token validation)
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = bool(form.remember_me.data)

        # Admin login: only allow username '215030' and password 'admin123'
        if username == '215030':
            if password == 'admin123':
                user = User.query.filter_by(username='215030').first()
                if user:
                    login_user(user, remember=remember_me)
                    session.permanent = True
                    next_page = request.args.get('next')
                    if not next_page or not next_page.startswith('/'):
                        next_page = url_for('dashboard')
                    return redirect(next_page)
                else:
                    flash('Admin user not found in database.', 'danger')
            else:
                flash('Invalid admin password.', 'danger')
            return redirect(url_for('index'))

        # Intern default login
        if username == 'dctraining' and password == 'Dctraining2023':
            user = User.query.filter_by(username='dctraining').first()
            if user:
                login_user(user, remember=remember_me)
                session.permanent = True
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('dashboard')
                return redirect(next_page)
            else:
                flash('Intern user not found in database.', 'danger')
            return redirect(url_for('index'))

        # Payroll login for users/interns
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact administrator.', 'danger')
                return redirect(url_for('index'))
            
            # Check if account is verified
            if not user.is_verified:
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('index'))
            
            # Check approval status for interns only
            if user.role == 'intern' and not user.is_approved:
                print(f"DEBUG: Intern {user.username} is not approved. is_approved={user.is_approved}, is_active={user.is_active}, role={user.role}")
                flash('Your intern account is pending admin approval. Please wait for activation.', 'warning')
                return redirect(url_for('index'))
            
            print(f"DEBUG: User {user.username} login SUCCESS - role={user.role}, is_approved={user.is_approved}, is_active={user.is_active}")
            
            login_user(user, remember=remember_me)
            session.permanent = True
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)

        flash('Invalid username or password', 'danger')
        return redirect(url_for('index'))

    # Render the index form on GET or failed validation
    return render_template('index.html', form=form)

@app.route('/logout')
@login_required
def logout():
    # Explicitly log out and clear session
    logout_user()
    session.clear()
    session.modified = True

    # Prepare redirect response and expire auth/session cookies to avoid automatic re-login
    resp = redirect(url_for('index'))

    # Determine remember cookie attributes from config
    remember_cookie = app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
    remember_domain = app.config.get('REMEMBER_COOKIE_DOMAIN', None)
    remember_path = app.config.get('REMEMBER_COOKIE_PATH', '/')

    # Session cookie attrs
    session_cookie = getattr(app, 'session_cookie_name', app.config.get('SESSION_COOKIE_NAME', 'session'))
    session_domain = app.config.get('SESSION_COOKIE_DOMAIN', None)
    session_path = app.config.get('SESSION_COOKIE_PATH', '/')

    # Expire cookies explicitly using matching path/domain where possible
    try:
        resp.set_cookie(remember_cookie, '', expires=0, path=remember_path, domain=remember_domain)
        resp.delete_cookie(remember_cookie, path=remember_path, domain=remember_domain)
    except Exception:
        resp.set_cookie(remember_cookie, '', expires=0, path='/')
        resp.delete_cookie(remember_cookie, path='/')

    try:
        resp.set_cookie(session_cookie, '', expires=0, path=session_path, domain=session_domain)
        resp.delete_cookie(session_cookie, path=session_path, domain=session_domain)
    except Exception:
        resp.set_cookie(session_cookie, '', expires=0, path='/')
        resp.delete_cookie(session_cookie, path='/')

    # Prevent caching so browser does not display stale authenticated pages
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'

    flash('You have been logged out.', 'info')
    return resp


@app.route('/keepalive')
@login_required
def keepalive():
    # Lightweight endpoint to refresh session last_activity from the client
    session.permanent = True
    session['last_activity'] = datetime.utcnow().isoformat()
    return jsonify({'ok': True})

from flask_wtf.csrf import CSRFError


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning(f"CSRFError: {e.description}")
    # flash('Your session expired or cookies are disabled. Please reload the login page and make sure cookies are enabled.', 'warning')
    return redirect(url_for('index'))


@app.route('/verify/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first_or_404()
    if user.is_verified:
        flash('Account already verified. Please login.', 'info')
    else:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your email has been verified. You can now login.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return render_template('register.html', form=form)

        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form)

        # Generate verification token
        token = str(uuid.uuid4())
        
        # Auto-approve users, require admin approval only for interns
        is_approved = form.role.data in ['admin', 'user']
        is_active = form.role.data in ['admin', 'user']
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
            phone_number=getattr(form, 'phone_number', None) and form.phone_number.data,
            is_verified=False,
            is_approved=is_approved,
            is_active=is_active,
            verification_token=token
        )
        try:
            db.session.add(user)
            db.session.flush()  # Get the user ID
        except Exception as e:
            db.session.rollback()
            print(f"Database error during user creation: {e}")
            flash('Registration failed. Please try again.', 'danger')
            return render_template('register.html', form=form)
        
        # Send verification email (only if email is configured)
        try:
            if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
                verify_url = url_for('verify_email', token=token, _external=True)
                msg = Message('Verify Your Email - ICT Helpdesk', recipients=[user.email])
                msg.body = f"Hello {user.full_name},\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nAfter verification, your account will need admin approval before you can access the system.\n\nIf you did not register, please ignore this email."
                mail.send(msg)
                email_sent = True
            else:
                email_sent = False
                # For development/testing, mark user as verified automatically
                user.is_verified = True
                user.verification_token = None
        except Exception as e:
            print(f"Email sending failed: {e}")
            email_sent = False
            # Mark user as verified automatically if email fails
            user.is_verified = True
            user.verification_token = None
        
        db.session.commit()
        
        # Notify all admins about new intern registration (users are auto-approved)
        if form.role.data == 'intern':
            NotificationManager.notify_new_user_registration(user)
        
        if form.role.data == 'user':
            if email_sent:
                flash('Registration successful! Please check your email to verify your account, then you can login.', 'info')
            else:
                flash('Registration successful! Your account has been automatically verified. You can now login.', 'info')
        else:  # intern
            if email_sent:
                flash('Registration successful! Please check your email to verify your account. Admin approval will be required before you can access the system.', 'info')
            else:
                flash('Registration successful! Your account has been automatically verified for testing. Admin approval will be required before you can access the system.', 'info')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    stats = get_dashboard_stats(current_user)

    # Show recent tickets: for users show tickets they created, for others show assigned tickets
    if current_user.role == 'user':
        recent_tickets = Ticket.query.filter_by(created_by_id=current_user.id).order_by(desc(Ticket.updated_at)).limit(5).all()
    else:
        recent_tickets = Ticket.query.join(Ticket.assignees).filter(User.id == current_user.id).order_by(desc(Ticket.updated_at)).limit(5).all()

    # Get system categories for reports upload
    system_categories = [c.name for c in Category.query.all()]

    return render_template('dashboard.html', stats=stats, recent_tickets=recent_tickets, system_categories=system_categories)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)

    stats = get_dashboard_stats(current_user)

    # Get recent activity with assignees eager-loaded
    recent_tickets = Ticket.query.options(joinedload(Ticket.assignees)).order_by(desc(Ticket.updated_at)).limit(10).all()

    # Get user statistics
    user_stats = db.session.query(
        User.role,
        func.count(User.id).label('count')
    ).filter(User.role != None).group_by(User.role).all()

    # Get pending intern approvals count
    pending_interns_count = User.query.filter_by(
        is_approved=False,
        is_verified=True,
        role='intern'
    ).count()

    # Get categories for dashboard display
    categories = Category.query.order_by(Category.name).all()
    system_categories = [c.name for c in categories]
    
    # Import CategoryForm for the modal
    from forms import CategoryForm
    category_form = CategoryForm()
    
    # Get escalated tickets for admin dashboard
    escalated_tickets = Ticket.query.options(
        joinedload(Ticket.escalated_by),
        joinedload(Ticket.creator)
    ).filter(Ticket.status == 'escalated').order_by(desc(Ticket.escalated_at)).all()

    return render_template('admin_dashboard.html', 
                         stats=stats, 
                         recent_tickets=recent_tickets, 
                         user_stats=user_stats,
                         pending_interns_count=pending_interns_count,
                         categories=categories,
                         system_categories=system_categories,
                         category_form=category_form,
                         escalated_tickets=escalated_tickets)

@app.route('/tickets')
@login_required
def tickets_list():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')

    query = Ticket.query

    # Apply role-based filtering
    if current_user.role == 'user':
        query = query.filter_by(created_by_id=current_user.id)
    elif current_user.role == 'intern':
        # By default interns see tickets they created OR are assigned to
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Ticket.created_by_id == current_user.id,
                Ticket.assignees.any(id=current_user.id)
            )
        )
    # Admin can see all tickets

    # Apply filters
    if status_filter:
        # Support a special pseudo-status 'assigned' which means "tickets assigned to the current user".
        if status_filter == 'assigned':
            # For interns show tickets assigned to them; for admins show tickets with any assignee
            if current_user.role == 'intern':
                query = Ticket.query.filter(Ticket.assignees.any(id=current_user.id))
            else:
                query = query.filter(Ticket.assignees.any())
        else:
            query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)

    tickets = query.order_by(desc(Ticket.created_at)).paginate(
        page=page, per_page=10, error_out=False
    )

    return render_template('tickets_list.html', tickets=tickets, status_filter=status_filter, priority_filter=priority_filter)

@app.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    from models import User
    from sms_service import send_sms
    
    form = TicketForm()

    if form.validate_on_submit():
        # Get selected assignees Users and interns submit unassigned; only admins can assign on creation.
        if current_user.role == 'user':
            # Users always submit unassigned - admin will assign later
            assignee_ids = []
        elif current_user.role == 'intern':
            # Intern-created tickets are auto-assigned to an active admin so they get handled promptly.
            admin = User.query.filter_by(role='admin', is_active=True).order_by(User.id).first()
            if admin:
                assignee_ids = [admin.id]
            else:
                # Fallback to unassigned if no active admin found
                assignee_ids = []
        else:  # admin
            assignee_ids = form.assignees.data or []
        # Priority-based limits
        max_assignees = 1
        if form.priority.data == 'urgent':
            max_assignees = 3
        elif form.priority.data == 'high':
            max_assignees = 4
        elif form.priority.data == 'low':
            max_assignees = 1
        if len(assignee_ids) > max_assignees:
            flash(f'Maximum {max_assignees} assignees allowed for {form.priority.data.title()} priority.', 'danger')
            return render_template('ticket_form.html', form=form, title='New Ticket')
        # Limit: Only 1 active (open/in_progress) ticket per intern/technician
        if assignee_ids:
            for assigned_to_id in assignee_ids:
                active_task_count = Ticket.query.join(Ticket.assignees).filter(
                    User.id == assigned_to_id,
                    Ticket.status.in_(['open', 'in_progress'])
                ).count()
                if active_task_count >= 1:
                    flash('This technician/intern already has an active task assigned. Only 1 active task is allowed at a time.', 'danger')
                    return render_template('ticket_form.html', form=form, title='New Ticket')

        nairobi_tz = pytz.timezone('Africa/Nairobi')
        now_nairobi = datetime.now(nairobi_tz)
        # Compose location string from department/subunit/location dropdowns
        loc_parts = []
        # Department (named `location_department` in the form)
        dept = form.location_department.data if hasattr(form, 'location_department') else None
        if dept:
            loc_parts.append(dept)
        # Subunit (optional)
        subunit = form.location_subunit.data if hasattr(form, 'location_subunit') else None
        if subunit:
            loc_parts.append(subunit)
        # Specific location/detail
        detail = form.location.data if hasattr(form, 'location') else None
        if detail:
            loc_parts.append(detail)

        location = ' - '.join([p for p in loc_parts if p]) if loc_parts else (form.location.data if hasattr(form, 'location') and form.location.data else '')
        # If University MIS System Issue, append subcategory to description (only for admins)
        description = form.description.data
        if current_user.role == 'admin' and hasattr(form, 'category_id') and form.category_id.data:
            category_obj = Category.query.get(form.category_id.data)
            if category_obj and category_obj.name == 'University MIS System Issue' and hasattr(form, 'mis_subcategory') and form.mis_subcategory.data:
                description = f"[{form.mis_subcategory.data}] " + description

        ticket = Ticket(
            location=location,
            description=description,
            priority=form.priority.data if current_user.role == 'admin' and hasattr(form, 'priority') and form.priority.data else 'low',
            created_by_id=current_user.id,
            category_id=form.category_id.data if current_user.role == 'admin' and hasattr(form, 'category_id') and form.category_id.data else None,
            status='in_progress' if assignee_ids else 'open',
            created_at=now_nairobi,
            updated_at=now_nairobi
        )
        db.session.add(ticket)
        db.session.flush()

        from sms_service import send_sms
        # Notify the creator via SMS
        creator_phone = getattr(current_user, 'phone_number', None)
        if creator_phone:
            send_sms(
                creator_phone,
                f"Your ticket #{ticket.id} has been created successfully. Status: {ticket.status}")

        # If ticket is unassigned (user role), notify all active admins via SMS
        if current_user.role == 'user' and not assignee_ids:
            admins = User.query.filter_by(role='admin', is_active=True).all()
            for admin in admins:
                admin_phone = getattr(admin, 'phone_number', None)
                if admin_phone:
                    send_sms(
                        admin_phone,
                        f"New unassigned ticket #{ticket.id} from {current_user.full_name}. Priority: {ticket.priority}. Please review.")

        # Assign users
        for uid in assignee_ids:
            user = User.query.get(uid)
            if user:
                ticket.assignees.append(user)

        # Handle file upload
        if form.attachments.data and form.attachments.data.filename:
            file = form.attachments.data
            filename = secure_filename(file.filename)
            if filename:
                try:
                    # Generate unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    attachment = Attachment(
                        filename=filename,
                        original_filename=file.filename,
                        file_size=os.path.getsize(file_path),
                        content_type=file.content_type,
                        ticket_id=ticket.id,
                        uploaded_by_id=current_user.id
                    )
                    db.session.add(attachment)
                except Exception as e:
                    flash(f'Error uploading file: {str(e)}', 'danger')
                    return render_template('ticket_form.html', form=form, title='New Ticket')

        db.session.commit()

        # Note: assignee_ids may be a list; notify each assignee if present
        if assignee_ids:
            for aid in assignee_ids:
                assignee = User.query.get(aid)
                assignee_phone = getattr(assignee, 'phone_number', None) if assignee else None
                if assignee and assignee_phone:
                    send_sms(
                        assignee_phone,
                        f"You have been assigned ticket #{ticket.id}. Please review it."
                    )

        # Send notifications using the new system
        print(f"DEBUG: About to send notifications for new ticket {ticket.id}")
        NotificationManager.notify_new_ticket(ticket)
        print(f"DEBUG: Notifications sent for ticket {ticket.id}")

        flash('Ticket created successfully', 'success')
        return redirect(url_for('ticket_detail', id=ticket.id))

    return render_template('ticket_form.html', form=form, title='New Ticket')

@app.route('/ticket/<int:id>')
@login_required
def ticket_detail(id):
    ticket = Ticket.query.get_or_404(id)

    # Check permissions (admin can access any ticket)
    if current_user.role == 'user' and ticket.created_by_id != current_user.id:
        abort(403)
    elif current_user.role == 'intern' and current_user.id not in [u.id for u in ticket.assignees] and ticket.created_by_id != current_user.id:
        abort(403)
    # Admin has access to all tickets - no restriction needed

    # Get comments based on user role
    if current_user.role == 'user':
        comments = Comment.query.filter_by(ticket_id=id, is_internal=False).order_by(Comment.created_at).all()
    else:
        comments = Comment.query.filter_by(ticket_id=id).order_by(Comment.created_at).all()

    comment_form = CommentForm()
    update_form = None
    if current_user.role in ['admin', 'intern']:
        update_form = TicketUpdateForm(user_role=current_user.role, current_status=ticket.status, obj=ticket)
        update_form.status.data = ticket.status
        update_form.priority.data = ticket.priority
        update_form.category_id.data = ticket.category_id if ticket.category_id else 0
        update_form.assignees.data = [u.id for u in ticket.assignees]

    # Check if intern can escalate this ticket (created by them or assigned to them, not already escalated or closed)
    can_escalate = current_user.role == 'intern' and (ticket.created_by_id == current_user.id or current_user.id in [u.id for u in ticket.assignees]) and ticket.status not in ['closed', 'escalated']

    return render_template('ticket_detail.html', ticket=ticket, comments=comments, 
                         comment_form=comment_form, update_form=update_form, can_escalate=can_escalate)

@app.route('/ticket/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    ticket = Ticket.query.get_or_404(id)

    # Check permissions (admin can comment on any ticket)
    if current_user.role == 'user' and ticket.created_by_id != current_user.id:
        abort(403)
    elif current_user.role == 'intern' and current_user.id not in [u.id for u in ticket.assignees] and ticket.created_by_id != current_user.id:
        abort(403)
    # Admin has access to all tickets - no restriction needed

    form = CommentForm()
    if form.validate_on_submit():
        # Users cannot create internal comments
        is_internal = form.is_internal.data if current_user.role in ['admin', 'intern'] else False

        comment = Comment(
            content=form.content.data,
            is_internal=is_internal,
            ticket_id=id,
            author_id=current_user.id
        )
        db.session.add(comment)

        # Update ticket timestamp
        ticket.updated_at = datetime.utcnow()
        db.session.commit()

        # Send notifications using the new system
        NotificationManager.notify_new_comment(ticket, current_user)

        flash('Comment added successfully', 'success')

    return redirect(url_for('ticket_detail', id=id))


@app.route('/ticket/<int:id>/escalate', methods=['POST'])
@login_required
def escalate_ticket(id):
    """Allow interns to escalate a ticket to all active admins with a required reason."""
    from forms import EscalationForm
    from models import TicketHistory
    
    ticket = Ticket.query.get_or_404(id)

    # Permission: only interns can escalate, and only for tickets they created or are assigned to
    if current_user.role != 'intern':
        abort(403)
    if not (ticket.created_by_id == current_user.id or current_user.id in [u.id for u in ticket.assignees]):
        abort(403)
    
    # Can't escalate closed or already escalated tickets
    if ticket.status in ['closed', 'escalated']:
        flash('This ticket cannot be escalated.', 'warning')
        return redirect(url_for('ticket_detail', id=id))

    form = EscalationForm()
    if form.validate_on_submit():
        reason = form.reason.data
        increase_priority = form.increase_priority.data
        
        old_status = ticket.status
        old_priority = ticket.priority
        
        # Update ticket status to escalated
        ticket.status = 'escalated'
        ticket.escalated_at = datetime.utcnow()
        ticket.escalated_by_id = current_user.id
        ticket.escalation_reason = reason
        ticket.updated_at = datetime.utcnow()
        
        # Optionally increase priority to urgent
        if increase_priority and ticket.priority != 'urgent':
            ticket.priority = 'urgent'
        
        # Unassign the current technician (ticket goes back to admin pool)
        old_assignees = [u.id for u in ticket.assignees]
        ticket.assignees = []
        
        # Log status change in history
        history = TicketHistory(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action='escalated',
            field_changed='status',
            old_value=old_status,
            new_value='escalated'
        )
        db.session.add(history)
        
        # Log priority change if applicable
        if old_priority != ticket.priority:
            priority_history = TicketHistory(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='priority increased on escalation',
                field_changed='priority',
                old_value=old_priority,
                new_value=ticket.priority
            )
            db.session.add(priority_history)
        
        # Log escalation reason
        reason_history = TicketHistory(
            ticket_id=ticket.id,
            user_id=current_user.id,
            action='escalation reason',
            field_changed='escalation_reason',
            old_value=None,
            new_value=reason[:200]
        )
        db.session.add(reason_history)
        
        db.session.commit()

        # Notify all active admins
        admins = User.query.filter_by(role='admin', is_active=True).all()
        for admin in admins:
            try:
                NotificationManager.create_notification(
                    user_id=admin.id,
                    ticket_id=ticket.id,
                    notification_type='escalation',
                    title=f'Escalation: Ticket #{ticket.id}',
                    message=f'Ticket #{ticket.id} has been escalated by {current_user.full_name}.\n\nReason: {reason}\n\nLocation: {ticket.location}\nPriority: {ticket.priority}'
                )
            except Exception as e:
                print(f"Error creating escalation notification for admin {admin.id}: {e}")

        # Send escalation emails to active admins if mail is configured
        try:
            admin_emails = [a.email for a in admins if a.email]
            if admin_emails and app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
                priority_prefix = "🔴 URGENT:" if ticket.priority == 'urgent' else "🟠 HIGH:" if ticket.priority == 'high' else "🟡 MEDIUM:" if ticket.priority == 'medium' else "🟢 LOW:"
                subject = f"{priority_prefix} Ticket #{ticket.id} Escalated - {ticket.location}"
                
                ticket_url = url_for('ticket_detail', id=ticket.id, _external=True)
                
                html_body = render_template('email_escalation.html',
                    ticket_id=ticket.id,
                    location=ticket.location,
                    priority=ticket.priority,
                    description=ticket.description,
                    escalated_by=current_user.full_name,
                    escalation_reason=reason,
                    ticket_url=ticket_url
                )
                
                text_body = (
                    f"Ticket #{ticket.id} has been escalated by {current_user.full_name}.\n\n"
                    f"Reason: {reason}\n\n"
                    f"Location: {ticket.location}\nPriority: {ticket.priority}\n\n"
                    f"Description:\n{ticket.description}\n\n"
                    f"View ticket: {ticket_url}\n\n"
                    "Please log in to the ICT Helpdesk to manage this ticket."
                )
                
                msg = Message(subject, recipients=admin_emails)
                msg.body = text_body
                msg.html = html_body
                mail.send(msg)
        except Exception as e:
            print(f"Error sending escalation emails: {e}")

        flash('Ticket escalated successfully. An admin will review it shortly.', 'success')
    else:
        if form.errors:
            for field, errors in form.errors.items():
                flash(f'{errors[0]}', 'danger')
        else:
            flash('Please provide a reason for escalation (minimum 10 characters).', 'warning')
    
    return redirect(url_for('ticket_detail', id=id))

@app.route('/ticket/<int:id>/update', methods=['POST'])
@login_required
def update_ticket(id):
    if current_user.role not in ['admin', 'intern']:
        abort(403)

    ticket = Ticket.query.get_or_404(id)

    # Interns can only update tickets assigned to them
    if current_user.role == 'intern' and current_user not in ticket.assignees:
        abort(403)

    form = TicketUpdateForm(user_role=current_user.role, current_status=ticket.status)
    
    # Debug logging  
    print(f"DEBUG UPDATE TICKET: method={request.method}, status={request.form.get('status')}, category_id={request.form.get('category_id')}")
    print(f"DEBUG CHOICES: {form.status.choices}")
    
    if form.validate_on_submit():
        print("DEBUG: Form validated successfully!")
        old_status = ticket.status
        old_priority = ticket.priority
        old_category_id = ticket.category_id
        old_assignees = set([u.id for u in ticket.assignees])

        # Prevent interns from closing tickets
        if current_user.role == 'intern' and form.status.data == 'closed':
            flash('Interns cannot close tickets. Only admins and ticket creators can close tickets.', 'danger')
            return redirect(url_for('ticket_detail', id=id))

        # Prevent interns from reverting resolved tickets
        if current_user.role == 'intern' and old_status == 'resolved' and form.status.data != 'resolved':
            flash('Interns cannot revert resolved tickets. Only administrators can modify resolved tickets.', 'danger')
            return redirect(url_for('ticket_detail', id=id))

        # Prevent reverting closed tickets
        if old_status == 'closed' and form.status.data != 'closed':
            flash('Cannot revert a closed ticket. Closed tickets cannot be reopened.', 'danger')
            return redirect(url_for('ticket_detail', id=id))

        # Only admins can de-escalate (change escalated status to another status)
        if old_status == 'escalated' and form.status.data != 'escalated' and current_user.role != 'admin':
            flash('Only administrators can de-escalate tickets.', 'danger')
            return redirect(url_for('ticket_detail', id=id))

        # Prevent closing tickets that are not resolved
        if form.status.data == 'closed' and old_status != 'resolved':
            flash('Tickets can only be closed if they are resolved first.', 'danger')
            return redirect(url_for('ticket_detail', id=id))

        # Category is required when resolving a ticket
        if form.status.data == 'resolved' and (not form.category_id.data or form.category_id.data == 0):
            flash('Category is required when resolving a ticket. Please select a category.', 'danger')
            return redirect(url_for('ticket_detail', id=id))

        # Prevent category changes on closed tickets
        if old_status == 'closed':
            flash('Cannot modify a closed ticket.', 'danger')
            return redirect(url_for('ticket_detail', id=id))

        # Status transition handling: Clear escalation data when moving back to in-progress
        if (old_status == 'escalated' or ticket.status == 'escalated') and form.status.data == 'in_progress':
            ticket.escalated_at = None
            ticket.escalated_by_id = None
            ticket.escalation_reason = None
            
            # Log de-escalation
            from models import TicketHistory
            de_esc_history = TicketHistory(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='de-escalated',
                field_changed='status',
                old_value='escalated',
                new_value='in_progress'
            )
            db.session.add(de_esc_history)
            
            # Add internal comment about de-escalation
            from models import Comment
            de_esc_comment = Comment(
                content=f"Ticket de-escalated and reassigned to: {', '.join([u.full_name for u in ticket.assignees]) if ticket.assignees else 'Unassigned'}",
                is_internal=True,
                ticket_id=ticket.id,
                author_id=current_user.id
            )
            db.session.add(de_esc_comment)

        ticket.status = form.status.data
        
        # Only admins can change priority; interns cannot edit priority
        if current_user.role == 'admin':
            ticket.priority = form.priority.data
        
        # Update category - admins can always update, interns only when resolving
        if current_user.role == 'admin':
            ticket.category_id = form.category_id.data if form.category_id.data != 0 else None
        elif current_user.role == 'intern' and form.status.data == 'resolved':
            ticket.category_id = form.category_id.data if form.category_id.data != 0 else None
        
        ticket.updated_at = datetime.utcnow()

        # Only admins can reassign tickets
        if current_user.role == 'admin':
            # Get new assignee IDs from form (should be a list)
            new_assignee_ids = form.assignees.data or []
            
            # Automatic transition: If reassigned while escalated or open, move to in_progress
            if (ticket.status in ['open', 'escalated']) and new_assignee_ids:
                ticket.status = 'in_progress'
                # Sync form status so subsequent logic sees the updated status
                form.status.data = 'in_progress'

            # Prevent assigning if intern/technician already has an active task
            for new_assigned_id in new_assignee_ids:
                active_task_count = Ticket.query.join(Ticket.assignees).filter(
                    User.id == new_assigned_id,
                    Ticket.status.in_(['open', 'in_progress']),
                    Ticket.id != ticket.id
                ).count()
                if active_task_count >= 1:
                    flash('This technician/intern already has an active task assigned. Only 1 active task is allowed at a time.', 'danger')
                    return render_template('ticket_detail.html', ticket=ticket, comments=Comment.query.filter_by(ticket_id=id).all(), comment_form=CommentForm(), update_form=form)
            
            # Update assignees and track newly assigned
            old_assignee_ids = set([u.id for u in ticket.assignees])
            ticket.assignees = [User.query.get(uid) for uid in new_assignee_ids if User.query.get(uid)]
            new_assigned_set = set(new_assignee_ids)
            
            # Send SMS to newly assigned staff (those not previously assigned)
            newly_assigned_ids = new_assigned_set - old_assignee_ids
            from sms_service import send_sms
            for newly_assigned_id in newly_assigned_ids:
                assignee = User.query.get(newly_assigned_id)
                assignee_phone = getattr(assignee, 'phone_number', None) if assignee else None
                if assignee and assignee_phone:
                    send_sms(
                        assignee_phone,
                        f"You have been assigned ticket #{ticket.id} - {ticket.location}. Priority: {ticket.priority}. Please review.")

            # Set due_date if assigned and not already set
            if new_assignee_ids and not ticket.due_date:
                ticket.due_date = datetime.utcnow() + timedelta(days=2)
            elif not new_assignee_ids:
                ticket.due_date = None

            # Auto-change status based on assignment
            if ticket.assignees and old_status == 'open':
                ticket.status = 'in_progress'
            elif not ticket.assignees and old_status == 'in_progress':
                ticket.status = 'open'

        # Set closed_at timestamp and closed_by if ticket is closed
        if form.status.data == 'closed' and old_status != 'closed':
            # Store current assignees before any modifications
            current_assignees = list(ticket.assignees)
            
            ticket.closed_at = datetime.utcnow()
            ticket.closed_by_id = current_user.id
            
            # CRITICAL: Ensure assignees are preserved when closing
            # This is essential for maintaining proper tracking and reports
            if current_user.role == 'admin' and form.assignees.data is not None:
                # If admin is reassigning during closure, use new assignees
                ticket.assignees = [User.query.get(uid) for uid in (form.assignees.data or []) if User.query.get(uid)]
            else:
                # Otherwise preserve existing assignees
                ticket.assignees = current_assignees
                
        elif form.status.data != 'closed':
            ticket.closed_at = None
            ticket.closed_by_id = None

        # Log history for status change
        if old_status != ticket.status:
            from models import TicketHistory
            history = TicketHistory(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='status changed',
                field_changed='status',
                old_value=old_status,
                new_value=ticket.status
            )
            db.session.add(history)
        # Log history for priority change
        if old_priority != ticket.priority:
            from models import TicketHistory
            history = TicketHistory(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='priority changed',
                field_changed='priority',
                old_value=old_priority,
                new_value=ticket.priority
            )
            db.session.add(history)
        # Log history for category change
        if old_category_id != ticket.category_id:
            from models import TicketHistory, Category
            old_cat_name = Category.query.get(old_category_id).name if old_category_id else 'Unclassified'
            new_cat_name = Category.query.get(ticket.category_id).name if ticket.category_id else 'Unclassified'
            history = TicketHistory(
                ticket_id=ticket.id,
                user_id=current_user.id,
                action='category changed',
                field_changed='category',
                old_value=old_cat_name,
                new_value=new_cat_name
            )
            db.session.add(history)
        # Log history for reassignment
        if current_user.role == 'admin':
            new_assignees = set([u.id for u in ticket.assignees])
            if old_assignees != new_assignees:
                from models import TicketHistory
                history = TicketHistory(
                    ticket_id=ticket.id,
                    user_id=current_user.id,
                    action='reassigned',
                    field_changed='assignees',
                    old_value=str(list(old_assignees)),
                    new_value=str(list(new_assignees))
                )
                db.session.add(history)

        db.session.commit()

        # Send notifications using the new system
        NotificationManager.notify_ticket_updated(ticket, current_user)

        flash('Ticket updated successfully', 'success')
    else:
        # Debug - form validation failed
        print(f"DEBUG VALIDATION FAILED: {form.errors}")
        if form.errors:
            for field, errors in form.errors.items():
                flash(f'Error in {field}: {", ".join(errors)}', 'danger')

    return redirect(url_for('ticket_detail', id=id))

@app.route('/ticket/<int:id>/print')
@login_required
def print_ticket(id):
    ticket = Ticket.query.get_or_404(id)

    # Check permissions - only allow printing of closed tickets
    if ticket.status != 'closed':
        abort(403)

    # Check if user has access to view this ticket
    if current_user.role == 'user' and ticket.created_by_id != current_user.id:
        abort(403)
    elif current_user.role == 'intern' and current_user.id not in [u.id for u in ticket.assignees] and ticket.created_by_id != current_user.id:
        abort(403)

    # Get all comments (internal comments only for admin/intern)
    if current_user.role == 'user':
        comments = Comment.query.filter_by(ticket_id=id, is_internal=False).order_by(Comment.created_at).all()
    else:
        comments = Comment.query.filter_by(ticket_id=id).order_by(Comment.created_at).all()

    return render_template('print_ticket.html', ticket=ticket, comments=comments)

@app.route('/ticket/<int:id>/close', methods=['POST'])
@login_required
def close_ticket(id):
    ticket = Ticket.query.get_or_404(id)

    # Check permissions - only admins and ticket creators can close tickets
    if current_user.role != 'admin' and ticket.created_by_id != current_user.id:
        abort(403)

    # Check if ticket is already closed
    if ticket.status == 'closed':
        flash('Ticket is already closed', 'info')
        return redirect(url_for('ticket_detail', id=id))

    # Check if ticket is resolved before closing
    if ticket.status != 'resolved':
        flash('Ticket must be resolved before it can be closed', 'danger')
        return redirect(url_for('ticket_detail', id=id))

    # Store assignees before closing to ensure they're preserved
    original_assignees = list(ticket.assignees)
    
    ticket.status = 'closed'
    ticket.closed_at = datetime.utcnow()
    ticket.closed_by_id = current_user.id
    ticket.updated_at = datetime.utcnow()
    
    # Ensure assignees are preserved - this is critical for reports and tracking
    ticket.assignees = original_assignees

    # Log the closure
    from models import TicketHistory
    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        action='ticket closed',
        field_changed='status',
        old_value='resolved',
        new_value='closed'
    )
    db.session.add(history)
    db.session.commit()

    # Send SMS to ticket creator when ticket is closed/resolved
    creator_phone = getattr(ticket.creator, 'phone_number', None) if ticket.creator else None
    if creator_phone:
        from sms_service import send_sms
        send_sms(
            creator_phone,
            f"Your ticket #{ticket.id} - {ticket.location} has been resolved. Status: Closed.")

    # Send notifications using the new system
    NotificationManager.notify_ticket_closed(ticket, current_user)

    flash('Ticket closed successfully', 'success')
    return redirect(url_for('ticket_detail', id=id))

@app.route('/reports/pdf')
@login_required
def reports_pdf():
    if current_user.role != 'admin':
        abort(403)

    # Use same logic as main reports route for consistency
    date_range = request.args.get('date_range', 'monthly')
    end_date = datetime.utcnow()
    
    # Custom date range takes precedence
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')
    if custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end, '%Y-%m-%d') + timedelta(days=1)
            days = (end_date - start_date).days
        except ValueError:
            if date_range == 'daily':
                start_date = end_date - timedelta(days=1)
                days = 1
            elif date_range == 'weekly':
                start_date = end_date - timedelta(days=7)
                days = 7
            elif date_range == 'monthly':
                start_date = end_date - timedelta(days=30)
                days = 30
            else:
                start_date = end_date - timedelta(days=365)
                days = 365
    else:
        # Calculate start date based on range
        if date_range == 'daily':
            start_date = end_date - timedelta(days=1)
            days = 1
        elif date_range == 'weekly':
            start_date = end_date - timedelta(days=7)
            days = 7
        elif date_range == 'monthly':
            start_date = end_date - timedelta(days=30)
            days = 30
        else:
            start_date = end_date - timedelta(days=365)
            days = 365

    # Filter parameters
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    category_filter = request.args.get('category', type=int)
    department_filter = request.args.get('department', '')

    # Build ticket query with filters
    ticket_query = Ticket.query.filter(
        Ticket.created_at >= start_date,
        Ticket.created_at <= end_date
    )

    if status_filter:
        ticket_query = ticket_query.filter(Ticket.status == status_filter)
    if priority_filter:
        ticket_query = ticket_query.filter(Ticket.priority == priority_filter)
    if category_filter:
        ticket_query = ticket_query.filter(Ticket.category_id == category_filter)
    if department_filter:
        ticket_query = ticket_query.filter(Ticket.location.contains(department_filter))

    tickets = ticket_query.all()

    # Calculate statistics
    total_tickets = len(tickets)
    closed_tickets = len([t for t in tickets if t.status == 'closed'])

    # Staff performance - count all assigned tickets regardless of status
    staff_performance = db.session.query(
        User.full_name,
        User.role,
        func.count(Ticket.id).label('tickets_handled')
    ).join(User.assigned_tickets)\
     .filter(
         Ticket.created_at >= start_date,
         Ticket.created_at <= end_date,
         User.role.in_(['admin', 'intern'])
     ).group_by(User.id, User.full_name, User.role).all()

    # Category stats
    category_stats = db.session.query(
        Category.name,
        func.count(Ticket.id).label('count')
    ).join(Ticket, Category.id == Ticket.category_id)\
     .filter(Ticket.created_at >= start_date, Ticket.created_at <= end_date)

    if category_filter:
        category_stats = category_stats.filter(Category.id == category_filter)

    category_stats = category_stats.group_by(Category.name).all()

    # Priority and status stats
    priority_stats = {}
    status_stats = {}
    for t in tickets:
        priority_stats[t.priority] = priority_stats.get(t.priority, 0) + 1
        status_stats[t.status] = status_stats.get(t.status, 0) + 1

    priority_stats = [{'priority': k, 'count': v} for k, v in priority_stats.items()]
    status_stats = [{'status': k, 'count': v} for k, v in status_stats.items()]

    # Average resolution time
    resolved_tickets = [t for t in tickets if t.status in ['resolved', 'closed'] and t.closed_at]
    avg_resolution_time = None
    if resolved_tickets:
        total_time = sum([(t.closed_at - t.created_at).total_seconds() for t in resolved_tickets])
        avg_resolution_time = total_time / len(resolved_tickets) / 3600  # in hours

    return render_template('reports_pdf.html',
                         total_tickets=total_tickets,
                         closed_tickets=closed_tickets,
                         staff_performance=staff_performance,
                         category_stats=category_stats,
                         status_stats=status_stats,
                         priority_stats=priority_stats,
                         avg_resolution_time=avg_resolution_time,
                         tickets=tickets[:50],  # Limit for PDF
                         days=days,
                         start_date=start_date.strftime('%Y-%m-%d'),
                         end_date=end_date.strftime('%Y-%m-%d'),
                         generated_date=datetime.utcnow())

@app.route('/reports')
@login_required
def reports():
    if current_user.role != 'admin':
        abort(403)

    # Enhanced filters with new date range options
    date_range = request.args.get('date_range', 'all')  # Default to all for broader range
    end_date = datetime.utcnow()
    
    # Custom date range takes precedence
    custom_start = request.args.get('start_date')
    custom_end = request.args.get('end_date')
    if custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end, '%Y-%m-%d') + timedelta(days=1)  # Include end date
            days = (end_date - start_date).days
        except ValueError:
            # Fall back to all data if custom dates are invalid
            start_date = datetime(2020, 1, 1)  # Very early date to capture all tickets
            days = (end_date - start_date).days
    else:
        # Calculate start date based on range
        if date_range == 'daily':
            start_date = end_date - timedelta(days=1)
            days = 1
        elif date_range == 'weekly':
            start_date = end_date - timedelta(days=7)
            days = 7
        elif date_range == 'monthly':
            start_date = end_date - timedelta(days=30)
            days = 30
        elif date_range == 'yearly':
            start_date = end_date - timedelta(days=365)
            days = 365
        else:  # 'all' or any unrecognized value
            # Use a very early date to capture all tickets
            start_date = datetime(2020, 1, 1)
            days = (end_date - start_date).days

    # Filter parameters
    created_by = request.args.get('created_by', type=int)
    attended_by = request.args.get('attended_by', type=int)
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    category_filter = request.args.get('category', type=int)
    department_filter = request.args.get('department', '')
    location_filter = request.args.get('location', '')
    subunit_filter = request.args.get('subunit', '')

    # All reference data for dropdowns
    all_users = User.query.order_by(User.full_name).all()
    all_categories = Category.query.order_by(Category.name).all()
    departments = ['SWA', 'UHS', 'Confucius']
    subunits = {
        'SWA': ['LSHR', 'USHR'],
        'UHS': ['Staff clinic', 'Student clinic', 'Account', 'Laboratory', 'ICEC', 'SickBay', 'Theatre', 'Gender Desk', 'CMO'],
        'Confucius': ['Block A', 'Block B', 'Block C', 'Auditorium', 'Library', 'Server Room']
    }
    locations = {
        'LSHR': ['Hall 1', 'Hall 2', 'Hall 3', 'Hall 10', 'SMU', 'CCU', 'Hall 15', 'Sport Department', 'Hall 11', 'Kitchen 1'],
        'USHR': ['Hall 4', 'Hall 5', 'Hall 6', 'Hall 7', 'Hall 8', 'Hall 9', 'Mamlaka Unit', 'SWA HQ']
    }

    # Build ticket query with enhanced filters
    ticket_query = Ticket.query.filter(
        Ticket.created_at >= start_date,
        Ticket.created_at <= end_date
    )

    if created_by:
        ticket_query = ticket_query.filter(Ticket.created_by_id == created_by)
    if attended_by:
        ticket_query = ticket_query.filter(Ticket.assignees.any(User.id == attended_by))
    if status_filter:
        ticket_query = ticket_query.filter(Ticket.status == status_filter)
    if priority_filter:
        ticket_query = ticket_query.filter(Ticket.priority == priority_filter)
    if category_filter:
        ticket_query = ticket_query.filter(Ticket.category_id == category_filter)
    if location_filter:
        ticket_query = ticket_query.filter(Ticket.location.contains(location_filter))
    elif subunit_filter:
        ticket_query = ticket_query.filter(Ticket.location.contains(subunit_filter))
    elif department_filter:
        ticket_query = ticket_query.filter(Ticket.location.contains(department_filter))

    tickets = ticket_query.all()
    
    # Debug information
    print(f"DEBUG: Reports query - Date range: {start_date} to {end_date}")
    print(f"DEBUG: Found {len(tickets)} tickets")
    if tickets:
        print(f"DEBUG: Sample ticket dates: {[t.created_at for t in tickets[:3]]}")

    # Enhanced statistics
    total_tickets = len(tickets)
    open_tickets = len([t for t in tickets if t.status == 'open'])
    in_progress_tickets = len([t for t in tickets if t.status == 'in_progress'])
    resolved_tickets = len([t for t in tickets if t.status == 'resolved'])
    closed_tickets = len([t for t in tickets if t.status == 'closed'])

    # Tickets by category
    category_stats = db.session.query(
        Category.name,
        func.count(Ticket.id).label('count')
    ).join(Ticket, Category.id == Ticket.category_id)\
     .filter(Ticket.created_at >= start_date, Ticket.created_at <= end_date)

    if category_filter:
        category_stats = category_stats.filter(Category.id == category_filter)
    if department_filter:
        category_stats = category_stats.filter(Ticket.location.contains(department_filter))

    category_stats = category_stats.group_by(Category.name).all()

    # Tickets by department/location
    department_stats = {}
    for ticket in tickets:
        dept = 'Other'
        # Check for more specific subunits first, then general departments
        for d in ['USHR', 'LSHR', 'Staff clinic', 'Student clinic', 'Block A', 'Block B', 'Block C', 'SWA', 'UHS', 'Confucius']:
            if d.lower() in ticket.location.lower():
                dept = d
                break
        department_stats[dept] = department_stats.get(dept, 0) + 1
    department_stats = [{'department': k, 'count': v} for k, v in department_stats.items()]

    # Staff performance - count all tickets assigned to staff, regardless of final status
    staff_performance = db.session.query(
        User.full_name,
        User.role,
        func.count(Ticket.id).label('tickets_handled')
    ).join(User.assigned_tickets)\
     .filter(
         Ticket.created_at >= start_date,
         Ticket.created_at <= end_date,
         User.role.in_(['admin', 'intern'])
     )

    if attended_by:
        staff_performance = staff_performance.filter(User.id == attended_by)

    staff_performance = staff_performance.group_by(User.id, User.full_name, User.role).all()
    
    print(f"DEBUG: Staff performance query returned {len(staff_performance)} results")
    print(f"DEBUG: Date range used: {start_date} to {end_date}")
    print(f"DEBUG: Total tickets found: {len(tickets)}")
    
    # If no staff performance but tickets exist, it means tickets are unassigned
    if len(tickets) > 0 and len(staff_performance) == 0:
        print("DEBUG: Tickets exist but no staff performance - likely unassigned tickets")

    # Response and resolution times
    tickets_with_times = [t for t in tickets if t.status in ['resolved', 'closed'] and t.closed_at]
    avg_resolution_time = None
    resolution_times = []

    if tickets_with_times:
        total_time = sum([(t.closed_at - t.created_at).total_seconds() for t in tickets_with_times])
        avg_resolution_time = total_time / len(tickets_with_times) / 3600  # in hours
        resolution_times = [
            {
                'ticket_id': t.id,
                'hours': (t.closed_at - t.created_at).total_seconds() / 3600
            } for t in tickets_with_times
        ]

    # Overdue tickets
    overdue_tickets = []
    for ticket in tickets:
        if ticket.due_date and ticket.status not in ['resolved', 'closed']:
            if datetime.utcnow() > ticket.due_date:
                overdue_tickets.append(ticket)

    # Priority distribution - ensure we have the stats in the expected format
    priority_dict = {}
    for t in tickets:
        priority_dict[t.priority] = priority_dict.get(t.priority, 0) + 1
    
    # Create priority_stats in both formats for template compatibility
    priority_stats = [{'priority': k, 'count': v} for k, v in priority_dict.items()]
    # Also create a direct dict for easy access in template
    priority_counts = {
        'urgent': priority_dict.get('urgent', 0),
        'high': priority_dict.get('high', 0),
        'medium': priority_dict.get('medium', 0),
        'low': priority_dict.get('low', 0)
    }

    # Status distribution
    status_stats = [
        {'status': 'open', 'count': open_tickets},
        {'status': 'in_progress', 'count': in_progress_tickets},
        {'status': 'resolved', 'count': resolved_tickets},
        {'status': 'closed', 'count': closed_tickets}
    ]

    # Trend data (last 7 days)
    trend_data = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        day_tickets = Ticket.query.filter(
            func.date(Ticket.created_at) == date.date()
        ).count()
        trend_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': day_tickets
        })
    trend_data.reverse()

    return render_template('reports.html',
                         total_tickets=total_tickets,
                         open_tickets=open_tickets,
                         in_progress_tickets=in_progress_tickets,
                         resolved_tickets=resolved_tickets,
                         closed_tickets=closed_tickets,
                         category_stats=category_stats,
                         department_stats=department_stats,
                         staff_performance=staff_performance,
                         priority_stats=priority_stats,
                         priority_counts=priority_counts,
                         status_stats=status_stats,
                         avg_resolution_time=avg_resolution_time,
                         resolution_times=resolution_times,
                         overdue_tickets=overdue_tickets,
                         trend_data=trend_data,
                         days=days,
                         start_date=start_date.strftime('%Y-%m-%d'),
                         end_date=end_date.strftime('%Y-%m-%d'),
                         datetime=datetime,
                         now=datetime.utcnow,
                         tickets=tickets,
                         all_users=all_users,
                         all_categories=all_categories,
                         departments=departments,
                         created_by=created_by or '',
                         attended_by=attended_by or '',
                         status_filter=status_filter,
                         priority_filter=priority_filter,
                         category_filter=category_filter or '',
                         department_filter=department_filter,
                         location_filter=location_filter,
                         subunit_filter=subunit_filter)

@app.route('/user-stats')
@login_required
@cache.cached(timeout=300, key_prefix='user_stats')
def get_user_stats():
    user_stats = db.session.query(
        User.role,
        func.count(User.id).label('count')
    ).filter(User.role != None).group_by(User.role).all()
    return jsonify(user_stats)

@app.route('/admin/users')
@login_required
def user_management():
    if current_user.role != 'admin':
        abort(403)

    users = User.query.all()
    form = UserManagementForm()
    admin_user_form = AdminUserForm()
    status_form = UserStatusForm()

    return render_template('user_management.html', users=users, form=form, 
                         admin_user_form=admin_user_form, status_form=status_form)

@app.route('/admin/users/update_password', methods=['POST'])
@login_required
def update_user_password():
    if current_user.role != 'admin':
        abort(403)

    form = UserManagementForm()
    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash(f'Password updated for {user.full_name}', 'success')

    return redirect(url_for('user_management'))

@app.route('/admin/categories', methods=['POST'])
@login_required
def add_category():
    if current_user.role != 'admin':
        abort(403)

    form = CategoryForm()
    if form.validate_on_submit():
        # Check if category already exists
        existing = Category.query.filter_by(name=form.name.data).first()
        if existing:
            flash('Category already exists', 'danger')
        else:
            category = Category(
                name=form.name.data,
                description=form.description.data
            )
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully', 'success')

    return redirect(url_for('user_management'))

@app.route('/admin/users/create', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        abort(403)

    form = AdminUserForm()
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists', 'danger')
            return redirect(url_for('user_management'))

        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email already registered', 'danger')
            return redirect(url_for('user_management'))

        # Auto-verify all accounts created by admin
        is_verified = True
        verification_token = None
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
            is_verified=is_verified,
            verification_token=verification_token
        )
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.full_name} created successfully', 'success')

    return redirect(url_for('user_management'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)

    user = User.query.get_or_404(user_id)

    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('user_management'))

    # Update tickets created by this user to show deleted user
    tickets_created = Ticket.query.filter_by(created_by_id=user_id).all()
    for ticket in tickets_created:
        ticket.created_by_id = None

    # Remove user from assignees for all tickets
    tickets_assigned = Ticket.query.join(Ticket.assignees).filter(User.id == user_id).all()
    for ticket in tickets_assigned:
        ticket.assignees = [u for u in ticket.assignees if u.id != user_id]
        if ticket.status == 'in_progress' and not ticket.assignees:
            ticket.status = 'open'

    # Update comments by this user
    comments = Comment.query.filter_by(author_id=user_id).all()
    for comment in comments:
        comment.author_id = None

    # Delete notifications for this user (notifications cannot exist without a user)
    Notification.query.filter_by(user_id=user_id).delete()

    # Delete notification settings for this user
    NotificationSettings.query.filter_by(user_id=user_id).delete()

    # Delete ticket history entries by this user
    from models import TicketHistory
    TicketHistory.query.filter_by(user_id=user_id).delete()

    # Delete the user
    db.session.delete(user)
    db.session.commit()

    flash(f'User {user.full_name} deleted successfully', 'success')
    return redirect(url_for('user_management'))

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    # Verify user has access to the file
    attachment = Attachment.query.filter_by(filename=filename).first_or_404()
    ticket = attachment.ticket

    # Check permissions
    if current_user.role == 'user' and ticket.created_by_id != current_user.id:
        abort(403)
    elif current_user.role == 'intern' and current_user.id not in [u.id for u in ticket.assignees]:
        abort(403)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    if current_user.role != 'admin':
        abort(403)

    ticket = Ticket.query.get_or_404(ticket_id)

    # Delete associated records in the correct order
    # Delete ticket history first
    from models import TicketHistory
    TicketHistory.query.filter_by(ticket_id=ticket_id).delete()

    # Delete comments and attachments
    Comment.query.filter_by(ticket_id=ticket_id).delete()
    Attachment.query.filter_by(ticket_id=ticket_id).delete()

    # Clear assignees (many-to-many relationship)
    ticket.assignees.clear()

    # Delete the ticket
    db.session.delete(ticket)
    db.session.commit()

    flash('Ticket deleted successfully', 'success')
    return redirect(url_for('tickets_list'))

@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Make datetime available in all templates
@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)

@app.route('/api/ticket_descriptions')
@login_required
def api_ticket_descriptions():
    # Only allow for authenticated users
    descriptions = db.session.query(Ticket.description).order_by(Ticket.created_at.desc()).limit(100).all()
    # Remove duplicates and short entries
    unique_desc = list({d[0].strip() for d in descriptions if d[0] and len(d[0].strip()) > 10})
    return jsonify(unique_desc)

@app.route('/api/mis_subcategories')
@login_required
def api_mis_subcategories():
    # Get MIS subcategories from tickets with category 'University MIS System Issue'
    mis_category = Category.query.filter_by(name='University MIS System Issue').first()
    if not mis_category:
        return jsonify([])
    descriptions = db.session.query(Ticket.description).filter(Ticket.category_id == mis_category.id).order_by(Ticket.created_at.desc()).limit(100).all()
    subcategories = []
    for desc in descriptions:
        if desc[0].startswith('[') and ']' in desc[0]:
            subcat = desc[0].split(']')[0][1:]  # Extract [subcat]
            if subcat and subcat not in subcategories:
                subcategories.append(subcat)
    return jsonify(subcategories)

@app.route('/api/notifications')
@login_required
def api_notifications():
    """Get notifications for current user"""
    print(f"DEBUG: Loading notifications for user {current_user.id}")
    notifications = NotificationManager.get_user_notifications(current_user.id, limit=20)
    print(f"DEBUG: Found {len(notifications)} notifications")
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'ticket_id': notification.ticket_id,
            'link': url_for('ticket_detail', id=notification.ticket_id) if notification.ticket_id else None
        })
    
    return jsonify(notification_data)

@app.route('/api/notifications/unread_count')
@login_required
def api_unread_count():
    """Get count of unread notifications"""
    count = NotificationManager.get_unread_count(current_user.id)
    print(f"DEBUG: Unread count for user {current_user.id}: {count}")
    return jsonify({'count': count})

@app.route('/api/notifications/<int:notification_id>/mark_read', methods=['POST'])
@login_required
def api_mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        success = NotificationManager.mark_as_read(notification_id, current_user.id)
        return jsonify({'success': success})
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifications/mark_all_read', methods=['POST'])
@login_required
def api_mark_all_read():
    """Mark all notifications as read"""
    try:
        count = NotificationManager.mark_all_as_read(current_user.id)
        return jsonify({'success': True, 'marked_count': count})
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifications/recent')
@login_required
def api_recent_notifications():
    """Get recent notifications since timestamp for real-time updates"""
    since_timestamp = request.args.get('since', type=int)
    if since_timestamp:
        since_datetime = datetime.fromtimestamp(since_timestamp / 1000)
        notifications = Notification.query.filter(
            Notification.user_id == current_user.id,
            Notification.created_at > since_datetime
        ).order_by(Notification.created_at.desc()).limit(10).all()
    else:
        notifications = []
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
            'ticket_id': notification.ticket_id,
            'link': url_for('ticket_detail', id=notification.ticket_id) if notification.ticket_id else None
        })
    
    return jsonify(notification_data)

@app.route('/api/notifications/clear_all', methods=['POST'])
@login_required
def api_clear_all_notifications():
    """Clear all notifications for current user"""
    try:
        count = NotificationManager.clear_all_notifications(current_user.id)
        return jsonify({'success': True, 'cleared_count': count})
    except Exception as e:
        print(f"Error clearing all notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug/tickets')
@login_required
def debug_tickets():
    """Debug route to inspect ticket data"""
    if current_user.role != 'admin':
        abort(403)
    
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(10).all()
    debug_data = []
    
    for ticket in tickets:
        debug_data.append({
            'id': ticket.id,
            'location': ticket.location,
            'status': ticket.status,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None,
            'assignees': [a.full_name for a in ticket.assignees] if ticket.assignees else []
        })
    
    total_count = Ticket.query.count()
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    recent_count = Ticket.query.filter(Ticket.created_at >= week_ago).count()
    
    return jsonify({
        'tickets': debug_data,
        'total_count': total_count,
        'recent_count': recent_count,
        'current_time': now.isoformat(),
        'week_ago': week_ago.isoformat()
    })

@app.route('/api/debug/notifications')
@login_required
def debug_notifications():
    """Debug route to inspect notification data"""
    if current_user.role != 'admin':
        abort(403)
    
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    debug_data = []
    
    for notif in notifications:
        debug_data.append({
            'id': notif.id,
            'user_id': notif.user_id,
            'type': notif.type,
            'title': notif.title,
            'is_read': notif.is_read,
            'created_at': notif.created_at.isoformat(),
            'read_at': notif.read_at.isoformat() if notif.read_at else None
        })
    
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    total_count = Notification.query.filter_by(user_id=current_user.id).count()
    
    return jsonify({
        'notifications': debug_data,
        'unread_count': unread_count,
        'total_count': total_count
    })


@app.route('/analytics')
@login_required
def analytics_dashboard():
    if current_user.role != 'admin':
        abort(403)

    # Quick stats for last 30 days
    start_date = datetime.utcnow() - timedelta(days=30)

    # Key performance indicators
    total_tickets = Ticket.query.filter(Ticket.created_at >= start_date).count()
    resolved_this_month = Ticket.query.filter(
        Ticket.created_at >= start_date,
        Ticket.status.in_(['resolved', 'closed'])
    ).count()

    # SLA compliance (assuming 2-day target)
    sla_compliant = 0
    sla_total = 0
    for ticket in Ticket.query.filter(
        Ticket.created_at >= start_date,
        Ticket.status.in_(['resolved', 'closed']),
        Ticket.closed_at.isnot(None)
    ).all():
        sla_total += 1
        resolution_time = (ticket.closed_at - ticket.created_at).total_seconds() / 3600
        if resolution_time <= 48:  # 48 hours = 2 days
            sla_compliant += 1

    sla_percentage = (sla_compliant / sla_total * 100) if sla_total > 0 else 0

    # Top categories
    top_categories = db.session.query(
        Category.name,
        func.count(Ticket.id).label('count')
    ).join(Ticket, Category.id == Ticket.category_id)\
     .filter(Ticket.created_at >= start_date)\
     .group_by(Category.name)\
     .order_by(func.count(Ticket.id).desc())\
     .limit(5).all()

    return render_template('analytics_dashboard.html',
                         total_tickets=total_tickets,
                         resolved_this_month=resolved_this_month,
                         sla_percentage=sla_percentage,
                         top_categories=top_categories)

@app.route('/notifications/settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """Manage notification settings for current user"""
    settings = NotificationSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = NotificationSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    
    form = NotificationSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        # Update settings from form
        form.populate_obj(settings)
        
        # Handle time fields specially - set to None if empty
        if form.dnd_start_time.data and form.dnd_start_time.data.strip():
            try:
                settings.dnd_start_time = datetime.strptime(form.dnd_start_time.data, '%H:%M').time()
            except ValueError:
                settings.dnd_start_time = None
        else:
            settings.dnd_start_time = None
            
        if form.dnd_end_time.data and form.dnd_end_time.data.strip():
            try:
                settings.dnd_end_time = datetime.strptime(form.dnd_end_time.data, '%H:%M').time()
            except ValueError:
                settings.dnd_end_time = None
        else:
            settings.dnd_end_time = None
        
        db.session.commit()
        flash('Notification settings updated successfully', 'success')
        return redirect(url_for('notification_settings'))
    
    return render_template('notification_settings.html', settings=settings, form=form)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allow users to change their own password"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not check_password_hash(current_user.password_hash, form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return render_template('change_password.html', form=form)
        
        # Update password
        current_user.password_hash = generate_password_hash(form.new_password.data)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html', form=form)

@app.route('/admin/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    """Admin route to activate/deactivate user accounts"""
    if current_user.role != 'admin':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'danger')
        return redirect(url_for('user_management'))
    
    # Toggle status
    user.is_active = not user.is_active
    status_text = 'activated' if user.is_active else 'deactivated'
    
    # If deactivating, remove from all assigned tickets
    if not user.is_active:
        tickets_assigned = Ticket.query.join(Ticket.assignees).filter(User.id == user_id).all()
        for ticket in tickets_assigned:
            ticket.assignees = [u for u in ticket.assignees if u.id != user_id]
            if ticket.status == 'in_progress' and not ticket.assignees:
                ticket.status = 'open'
    
    db.session.commit()
    flash(f'User {user.full_name} has been {status_text}', 'success')
    return redirect(url_for('user_management'))



@app.route('/admin/pending_users')
@login_required
def pending_users():
    """Show pending user approvals"""
    if current_user.role != 'admin':
        abort(403)
    
    # Get pending interns
    pending_interns = User.query.filter_by(
        is_approved=False,
        is_verified=True,
        role='intern'
    ).order_by(User.created_at.desc()).all()
    
    # Get approved interns for reference
    approved_interns = User.query.filter_by(
        is_approved=True,
        role='intern'
    ).order_by(User.created_at.desc()).limit(10).all()
    
    # Import csrf for token generation
    from flask_wtf.csrf import generate_csrf
    
    return render_template('pending_users.html', 
                         pending_interns=pending_interns, 
                         approved_interns=approved_interns,
                         csrf_token=generate_csrf)

@app.route('/admin/intern_management')
@login_required
def intern_management():
    """Dedicated intern management interface"""
    if current_user.role != 'admin':
        abort(403)
    
    # Get all interns with different statuses
    pending_interns = User.query.filter_by(
        is_approved=False,
        is_verified=True,
        role='intern'
    ).order_by(User.created_at.desc()).all()
    
    active_interns = User.query.filter_by(
        is_approved=True,
        is_active=True,
        role='intern'
    ).order_by(User.created_at.desc()).all()
    
    inactive_interns = User.query.filter_by(
        is_approved=True,
        is_active=False,
        role='intern'
    ).order_by(User.created_at.desc()).all()
    
    # Get intern performance statistics
    intern_stats = []
    for intern in active_interns:
        active_tickets = Ticket.query.join(Ticket.assignees).filter(
            User.id == intern.id,
            Ticket.status.in_(['open', 'in_progress'])
        ).count()
        
        completed_tickets = Ticket.query.join(Ticket.assignees).filter(
            User.id == intern.id,
            Ticket.status.in_(['resolved', 'closed'])
        ).count()
        
        intern_stats.append({
            'intern': intern,
            'active_tickets': active_tickets,
            'completed_tickets': completed_tickets
        })
    
    # Import csrf for token generation
    from flask_wtf.csrf import generate_csrf
    
    return render_template('intern_management.html', 
                         pending_interns=pending_interns,
                         active_interns=active_interns,
                         inactive_interns=inactive_interns,
                         intern_stats=intern_stats,
                         csrf_token=generate_csrf)

@app.route('/admin/staff_management')
@login_required
def staff_management():
    """Dedicated staff/user management interface"""
    if current_user.role != 'admin':
        abort(403)
    
    # Get all staff (non-intern users)
    staff_users = User.query.filter(User.role.in_(['user', 'admin'])).order_by(User.created_at.desc()).all()
    
    # Separate active and inactive staff
    active_staff = [u for u in staff_users if u.is_active]
    inactive_staff = [u for u in staff_users if not u.is_active]
    
    return render_template('staff_management.html', 
                         active_staff=active_staff,
                         inactive_staff=inactive_staff)

@app.route('/admin/users/<int:user_id>/approve', methods=['POST'])
@login_required
def approve_user_account(user_id):
    """Approve a pending user account"""
    if current_user.role != 'admin':
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    if user.is_approved:
        flash(f'{user.full_name} is already approved', 'info')
        return redirect(url_for('pending_users'))
    
    print(f"DEBUG: Approving user {user.username} - Current role: {user.role}")
    
    # Approve the user - preserve the original role
    user.is_approved = True
    user.is_active = True
    user.approved_by_id = current_user.id
    user.approved_at = datetime.utcnow()
    # DO NOT change the role - keep it as 'intern'
    
    db.session.commit()
    
    print(f"DEBUG: After approval - User {user.username} role: {user.role}, is_approved: {user.is_approved}, is_active: {user.is_active}")
    
    # Send notification to the approved user
    try:
        NotificationManager.notify_user_approved(user, current_user)
    except:
        pass  # Don't fail if notification fails
    
    flash(f'{user.full_name} (Intern) has been approved and can now login', 'success')
    return redirect(url_for('pending_users'))

@app.route('/api/current-timestamp', methods=['GET'])
def get_current_timestamp():
    return jsonify({"timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})

@app.route('/api/reports-data', methods=['GET'])
@login_required
def get_reports_data():
    task = generate_report_data.apply_async()
    return jsonify({"task_id": task.id})# Reports Management Routes
# Add these routes to routes.py at the end of the file

def get_file_category(filename, content_type):
    """Determine file category based on extension and content type."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    content_type_lower = (content_type or '').lower()

    # Map extensions and MIME types to categories
    if ext in ['pdf'] or 'pdf' in content_type_lower:
        return 'pdf'
    elif ext in ['csv'] or 'csv' in content_type_lower:
        return 'csv'
    elif ext in ['xlsx', 'xls'] or 'spreadsheet' in content_type_lower or 'excel' in content_type_lower:
        return 'excel'
    elif ext in ['docx', 'doc'] or 'word' in content_type_lower:
        return 'word'
    elif ext in ['pptx', 'ppt'] or 'presentation' in content_type_lower:
        return 'ppt'
    elif ext in ['txt'] or 'text' in content_type_lower:
        return 'text'
    elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp'] or 'image' in content_type_lower:
        return 'image'
    else:
        return 'other'


@app.route('/reports-management')
@login_required
def reports_management():
    """Main reports management page (accessible to admin and interns)."""
    if current_user.role not in ['admin', 'intern']:
        abort(403)

    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    uploader_filter = request.args.get('uploader', type=int)
    search_query = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    # Build base query
    query = ReportFile.query

    # Filter by role: admins see all, interns/users see only their own and team reports
    if current_user.role == 'admin':
        # Admin sees all reports
        pass
    elif current_user.role == 'intern':
        # Intern sees only their own reports
        query = query.filter_by(uploaded_by_id=current_user.id)

    # Apply filters
    if category_filter:
        query = query.filter_by(file_type=category_filter)
    if uploader_filter and current_user.role == 'admin':
        query = query.filter_by(uploaded_by_id=uploader_filter)
    if search_query:
        query = query.filter(ReportFile.original_filename.ilike(f'%{search_query}%'))
    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(ReportFile.uploaded_at >= start_date)
        except ValueError:
            pass
    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ReportFile.uploaded_at < end_date)
        except ValueError:
            pass

    # Order by most recent first
    reports = query.order_by(ReportFile.uploaded_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # Get unique categories and uploaders for filter dropdowns
    all_categories = db.session.query(ReportFile.file_type).distinct().all()
    file_categories = [c[0] for c in all_categories if c[0]]

    # Get system categories from Category model
    system_categories = [c.name for c in Category.query.all()]

    all_uploaders = []
    if current_user.role == 'admin':
        all_uploaders = User.query.filter(User.role.in_(['admin', 'intern'])).order_by(User.full_name).all()

    return render_template('reports_management.html',
                         reports=reports,
                         categories=file_categories,
                         system_categories=system_categories,
                         all_uploaders=all_uploaders,
                         category_filter=category_filter,
                         uploader_filter=uploader_filter,
                         search_query=search_query,
                         date_from=date_from,
                         date_to=date_to)


@app.route('/report/upload', methods=['POST'])
@login_required
def upload_report():
    """Upload a new report file."""
    if current_user.role not in ['admin', 'intern']:
        abort(403)

    if 'file' not in request.files:
        flash('No file part in request', 'danger')
        return redirect(url_for('reports_management'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('reports_management'))

    category = request.form.get('category', '')
    
    if not category:
        flash('Category is required', 'danger')
        return redirect(url_for('reports_management'))

    try:
        filename = secure_filename(file.filename)
        if not filename:
            flash('Invalid filename', 'danger')
            return redirect(url_for('reports_management'))

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        # Save file
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Determine file type (pdf, csv, excel, word, ppt, image, text, other)
        file_type = get_file_category(filename, file.content_type)

        # Create report record
        report = ReportFile(
            filename=unique_filename,
            original_filename=filename,
            file_size=file_size,
            content_type=file.content_type or 'application/octet-stream',
            file_type=file_type,
            category=category,
            uploaded_by_id=current_user.id
        )
        db.session.add(report)
        db.session.commit()

        # Success message suppressed to avoid popup after upload

    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading file: {str(e)}', 'danger')

    # Redirect back to the reports management page but suppress the flash popup there
    return redirect(url_for('reports_management', no_flash=1))


@app.route('/report/<int:report_id>/download')
@login_required
def download_report(report_id):
    """Download a report file."""
    report = ReportFile.query.get_or_404(report_id)

    # Permission check
    if current_user.role == 'intern' and report.uploaded_by_id != current_user.id:
        abort(403)

    # Log download
    print(f"DEBUG: User {current_user.username} downloading report {report.id}: {report.original_filename}")

    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], report.filename, as_attachment=True, download_name=report.original_filename)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(url_for('reports_management'))


@app.route('/report/<int:report_id>/delete', methods=['POST'])
@login_required
def delete_report(report_id):
    """Delete a report file (admin only or by uploader)."""
    report = ReportFile.query.get_or_404(report_id)

    # Permission check: only admin or the uploader can delete
    if current_user.role != 'admin' and report.uploaded_by_id != current_user.id:
        abort(403)

    try:
        # Delete file from disk
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], report.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete database record
        db.session.delete(report)
        db.session.commit()

        # Success message suppressed to avoid popup after delete

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting report: {str(e)}', 'danger')

    # Redirect back to the reports management page but suppress the flash popup there
    return redirect(url_for('reports_management', no_flash=1))


@app.route('/api/reports/stats')
@login_required
def api_reports_stats():
    """Get statistics about uploaded reports (for admin dashboard)."""
    if current_user.role != 'admin':
        abort(403)

    # Total reports
    total_reports = ReportFile.query.count()

    # Reports by file type
    category_stats = db.session.query(
        ReportFile.file_type,
        func.count(ReportFile.id).label('count')
    ).group_by(ReportFile.file_type).all()

    # Reports by uploader
    uploader_stats = db.session.query(
        User.full_name,
        func.count(ReportFile.id).label('count')
    ).join(ReportFile, User.id == ReportFile.uploaded_by_id).group_by(User.id, User.full_name).all()

    # Total file size
    total_size = db.session.query(func.sum(ReportFile.file_size)).scalar() or 0

    return jsonify({
        'total_reports': total_reports,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'category_stats': [{'category': c[0], 'count': c[1]} for c in category_stats],
        'uploader_stats': [{'uploader': u[0], 'count': u[1]} for u in uploader_stats]
    })
