"""
REST API routes for the React frontend.
All endpoints are under /api/v1/ and use JWT authentication.
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def user_to_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_active': user.is_active,
        'is_verified': user.is_verified,
        'is_approved': user.is_approved,
        'phone_number': user.phone_number,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'approved_at': user.approved_at.isoformat() if user.approved_at else None,
    }


def ticket_to_dict(ticket, include_comments=False, include_history=False):
    from models import Comment
    data = {
        'id': ticket.id,
        'location': ticket.location,
        'description': ticket.description,
        'status': ticket.status,
        'priority': ticket.priority,
        'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
        'updated_at': ticket.updated_at.isoformat() if ticket.updated_at else None,
        'closed_at': ticket.closed_at.isoformat() if ticket.closed_at else None,
        'due_date': ticket.due_date.isoformat() if ticket.due_date else None,
        'escalated_at': ticket.escalated_at.isoformat() if ticket.escalated_at else None,
        'escalation_reason': ticket.escalation_reason,
        'category': {'id': ticket.category.id, 'name': ticket.category.name} if ticket.category else None,
        'creator': {'id': ticket.creator.id, 'full_name': ticket.creator.full_name, 'username': ticket.creator.username} if ticket.creator else None,
        'assignees': [{'id': u.id, 'full_name': u.full_name, 'username': u.username} for u in ticket.assignees],
        'closed_by': {'id': ticket.closed_by.id, 'full_name': ticket.closed_by.full_name} if ticket.closed_by else None,
        'escalated_by': {'id': ticket.escalated_by.id, 'full_name': ticket.escalated_by.full_name} if ticket.escalated_by else None,
        'attachments': [attachment_to_dict(a) for a in ticket.attachments.all()],
        'comment_count': ticket.comments.count(),
    }
    if include_comments:
        data['comments'] = [comment_to_dict(c) for c in ticket.comments.order_by('created_at').all()]
    if include_history:
        data['history'] = [history_to_dict(h) for h in sorted(ticket.histories, key=lambda h: h.timestamp)]
    return data


def comment_to_dict(comment):
    return {
        'id': comment.id,
        'content': comment.content,
        'is_internal': comment.is_internal,
        'created_at': comment.created_at.isoformat() if comment.created_at else None,
        'author': {'id': comment.author.id, 'full_name': comment.author.full_name, 'role': comment.author.role} if comment.author else None,
    }


def history_to_dict(h):
    return {
        'id': h.id,
        'action': h.action,
        'field_changed': h.field_changed,
        'old_value': h.old_value,
        'new_value': h.new_value,
        'timestamp': h.timestamp.isoformat() if h.timestamp else None,
        'user': {'id': h.user.id, 'full_name': h.user.full_name} if h.user else None,
    }


def attachment_to_dict(a):
    return {
        'id': a.id,
        'original_filename': a.original_filename,
        'file_size': a.file_size,
        'content_type': a.content_type,
        'created_at': a.created_at.isoformat() if a.created_at else None,
        'url': f'/api/v1/attachments/{a.filename}',
    }


def notification_to_dict(n):
    return {
        'id': n.id,
        'type': n.type,
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat() if n.created_at else None,
        'ticket_id': n.ticket_id,
    }


def get_current_user():
    from models import User
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def record_history(ticket, user, action, field=None, old_val=None, new_val=None):
    from models import TicketHistory
    from app import db
    h = TicketHistory(
        ticket_id=ticket.id,
        user_id=user.id,
        action=action,
        field_changed=field,
        old_value=str(old_val) if old_val is not None else None,
        new_value=str(new_val) if new_val is not None else None,
    )
    db.session.add(h)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@api_bp.route('/auth/login', methods=['POST'])
def login():
    from models import User
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401

    # Special admin/intern hardcoded check (mirrors existing routes.py logic)
    if username == '215030':
        if password != 'admin123':
            return jsonify({'error': 'Invalid username or password'}), 401
    elif username == 'dctraining':
        if password != 'Dctraining2023':
            return jsonify({'error': 'Invalid username or password'}), 401
    else:
        if not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid username or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is deactivated. Contact administrator.'}), 403
    if not user.is_verified:
        return jsonify({'error': 'Email not verified. Please verify your email.'}), 403
    if user.role == 'intern' and not user.is_approved:
        return jsonify({'error': 'Intern account pending admin approval.'}), 403

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user_to_dict(user),
    }), 200


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({'access_token': access_token}), 200


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user_to_dict(user)), 200


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully'}), 200


@api_bp.route('/auth/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    from app import db
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    current_pw = data.get('current_password', '')
    new_pw = data.get('new_password', '')

    if not current_pw or not new_pw:
        return jsonify({'error': 'current_password and new_password are required'}), 400

    # Allow admin bypass for hardcoded accounts
    if user.username == '215030':
        if current_pw != 'admin123' and not check_password_hash(user.password_hash, current_pw):
            return jsonify({'error': 'Current password is incorrect'}), 400
    elif user.username == 'dctraining':
        if current_pw != 'Dctraining2023' and not check_password_hash(user.password_hash, current_pw):
            return jsonify({'error': 'Current password is incorrect'}), 400
    else:
        if not check_password_hash(user.password_hash, current_pw):
            return jsonify({'error': 'Current password is incorrect'}), 400

    if len(new_pw) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400

    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@api_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    from models import Ticket, User
    user = get_current_user()

    if user.role == 'admin':
        total = Ticket.query.count()
        open_t = Ticket.query.filter_by(status='open').count()
        in_progress = Ticket.query.filter_by(status='in_progress').count()
        resolved = Ticket.query.filter_by(status='resolved').count()
        closed = Ticket.query.filter_by(status='closed').count()
        escalated = Ticket.query.filter_by(status='escalated').count()
        pending_users = User.query.filter_by(role='intern', is_approved=False).count()
        recent_tickets = Ticket.query.order_by(desc(Ticket.created_at)).limit(5).all()
    elif user.role == 'intern':
        assigned = [t for t in user.assigned_tickets]
        assigned_ids = [t.id for t in assigned]
        total = len(assigned_ids)
        open_t = Ticket.query.filter(Ticket.id.in_(assigned_ids), Ticket.status == 'open').count() if assigned_ids else 0
        in_progress = Ticket.query.filter(Ticket.id.in_(assigned_ids), Ticket.status == 'in_progress').count() if assigned_ids else 0
        resolved = Ticket.query.filter(Ticket.id.in_(assigned_ids), Ticket.status == 'resolved').count() if assigned_ids else 0
        closed = Ticket.query.filter(Ticket.id.in_(assigned_ids), Ticket.status == 'closed').count() if assigned_ids else 0
        escalated = Ticket.query.filter(Ticket.id.in_(assigned_ids), Ticket.status == 'escalated').count() if assigned_ids else 0
        pending_users = 0
        recent_tickets = Ticket.query.filter(Ticket.id.in_(assigned_ids)).order_by(desc(Ticket.created_at)).limit(5).all() if assigned_ids else []
    else:
        total = Ticket.query.filter_by(created_by_id=user.id).count()
        open_t = Ticket.query.filter_by(created_by_id=user.id, status='open').count()
        in_progress = Ticket.query.filter_by(created_by_id=user.id, status='in_progress').count()
        resolved = Ticket.query.filter_by(created_by_id=user.id, status='resolved').count()
        closed = Ticket.query.filter_by(created_by_id=user.id, status='closed').count()
        escalated = Ticket.query.filter_by(created_by_id=user.id, status='escalated').count()
        pending_users = 0
        recent_tickets = Ticket.query.filter_by(created_by_id=user.id).order_by(desc(Ticket.created_at)).limit(5).all()

    return jsonify({
        'total': total,
        'open': open_t,
        'in_progress': in_progress,
        'resolved': resolved,
        'closed': closed,
        'escalated': escalated,
        'pending_users': pending_users,
        'recent_tickets': [ticket_to_dict(t) for t in recent_tickets],
    }), 200


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------
@api_bp.route('/tickets', methods=['GET'])
@jwt_required()
def list_tickets():
    from models import Ticket, User
    user = get_current_user()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')

    if user.role == 'admin':
        query = Ticket.query
    elif user.role == 'intern':
        assigned_ids = [t.id for t in user.assigned_tickets]
        if assigned_ids:
            query = Ticket.query.filter(Ticket.id.in_(assigned_ids))
        else:
            query = Ticket.query.filter(Ticket.id == -1)
    else:
        query = Ticket.query.filter_by(created_by_id=user.id)

    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if category_id:
        query = query.filter(Ticket.category_id == category_id)
    if search:
        query = query.filter(
            Ticket.description.ilike(f'%{search}%') |
            Ticket.location.ilike(f'%{search}%')
        )

    query = query.order_by(desc(Ticket.created_at))
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tickets': [ticket_to_dict(t) for t in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': paginated.page,
        'per_page': per_page,
    }), 200


@api_bp.route('/tickets', methods=['POST'])
@jwt_required()
def create_ticket():
    from app import app, db
    from models import Ticket, Category, User, TicketHistory, Notification
    from notification_utils import NotificationManager

    user = get_current_user()

    location = request.form.get('location', request.json.get('location', '') if request.is_json else '')
    description = request.form.get('description', request.json.get('description', '') if request.is_json else '')
    priority = request.form.get('priority', request.json.get('priority', 'medium') if request.is_json else 'medium')
    category_id = request.form.get('category_id', request.json.get('category_id') if request.is_json else None)
    assignee_ids = request.form.getlist('assignees') or (request.json.get('assignees', []) if request.is_json else [])

    if not location or not description:
        return jsonify({'error': 'Location and description are required'}), 400

    ticket = Ticket(
        location=location,
        description=description,
        priority=priority,
        status='open',
        created_by_id=user.id,
        category_id=int(category_id) if category_id and str(category_id) != '0' else None,
    )
    db.session.add(ticket)
    db.session.flush()

    # Assignees
    for aid in assignee_ids:
        try:
            assignee = User.query.get(int(aid))
            if assignee:
                ticket.assignees.append(assignee)
        except (ValueError, TypeError):
            pass

    # File attachments
    if 'attachments' in request.files:
        from models import Attachment
        for f in request.files.getlist('attachments'):
            if f and f.filename and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_name = f"{ts}_{filename}"
                path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                f.save(path)
                att = Attachment(
                    filename=unique_name,
                    original_filename=filename,
                    file_size=os.path.getsize(path),
                    content_type=f.content_type or 'application/octet-stream',
                    ticket_id=ticket.id,
                    uploaded_by_id=user.id,
                )
                db.session.add(att)

    record_history(ticket, user, 'created')
    db.session.commit()

    # Notify admins/interns
    try:
        NotificationManager.notify_new_ticket(ticket, user)
    except Exception as e:
        logger.warning(f"Notification error: {e}")

    return jsonify(ticket_to_dict(ticket)), 201


@api_bp.route('/tickets/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    from models import Ticket
    user = get_current_user()
    ticket = Ticket.query.get_or_404(ticket_id)

    # Permission check
    if user.role == 'user' and ticket.created_by_id != user.id:
        return jsonify({'error': 'Access denied'}), 403
    if user.role == 'intern':
        assigned_ids = [t.id for t in user.assigned_tickets]
        if ticket.id not in assigned_ids and ticket.created_by_id != user.id:
            return jsonify({'error': 'Access denied'}), 403

    return jsonify(ticket_to_dict(ticket, include_comments=True, include_history=True)), 200


@api_bp.route('/tickets/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    from app import db
    from models import Ticket, User, Category
    user = get_current_user()
    ticket = Ticket.query.get_or_404(ticket_id)

    if user.role == 'user':
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json(silent=True) or {}

    if 'status' in data:
        old = ticket.status
        new = data['status']
        if old != new:
            record_history(ticket, user, 'status changed', 'status', old, new)
            ticket.status = new
            ticket.updated_at = datetime.utcnow()

    if 'priority' in data and user.role == 'admin':
        old = ticket.priority
        new = data['priority']
        if old != new:
            record_history(ticket, user, 'priority changed', 'priority', old, new)
            ticket.priority = new

    if 'category_id' in data and user.role == 'admin':
        cat_id = data['category_id']
        ticket.category_id = int(cat_id) if cat_id and str(cat_id) != '0' else None

    if 'assignees' in data and user.role in ('admin',):
        ticket.assignees.clear()
        for aid in data['assignees']:
            assignee = User.query.get(int(aid))
            if assignee:
                ticket.assignees.append(assignee)
        record_history(ticket, user, 'assignees updated')

    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    # Notify
    try:
        from notification_utils import NotificationManager
        NotificationManager.notify_ticket_updated(ticket, user)
    except Exception as e:
        logger.warning(f"Notification error: {e}")

    return jsonify(ticket_to_dict(ticket, include_comments=True, include_history=True)), 200


@api_bp.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@jwt_required()
def delete_ticket(ticket_id):
    from app import db
    from models import Ticket
    user = get_current_user()

    if user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'Ticket deleted'}), 200


@api_bp.route('/tickets/<int:ticket_id>/comment', methods=['POST'])
@jwt_required()
def add_comment(ticket_id):
    from app import db
    from models import Ticket, Comment
    user = get_current_user()
    ticket = Ticket.query.get_or_404(ticket_id)

    if user.role == 'user' and ticket.created_by_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()
    is_internal = bool(data.get('is_internal', False)) and user.role in ('admin', 'intern')

    if not content:
        return jsonify({'error': 'Comment content is required'}), 400

    comment = Comment(
        content=content,
        is_internal=is_internal,
        ticket_id=ticket_id,
        author_id=user.id,
    )
    db.session.add(comment)
    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    try:
        from notification_utils import NotificationManager
        NotificationManager.notify_new_comment(ticket, comment, user)
    except Exception as e:
        logger.warning(f"Notification error: {e}")

    return jsonify(comment_to_dict(comment)), 201


@api_bp.route('/tickets/<int:ticket_id>/escalate', methods=['POST'])
@jwt_required()
def escalate_ticket(ticket_id):
    from app import db
    from models import Ticket
    user = get_current_user()

    if user.role not in ('intern', 'admin'):
        return jsonify({'error': 'Access denied'}), 403

    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json(silent=True) or {}
    reason = data.get('reason', '').strip()

    if not reason or len(reason) < 10:
        return jsonify({'error': 'Escalation reason must be at least 10 characters'}), 400

    ticket.status = 'escalated'
    ticket.escalated_at = datetime.utcnow()
    ticket.escalated_by_id = user.id
    ticket.escalation_reason = reason
    ticket.updated_at = datetime.utcnow()

    if data.get('increase_priority'):
        ticket.priority = 'urgent'

    record_history(ticket, user, 'escalated', 'status', ticket.status, 'escalated')
    db.session.commit()

    return jsonify(ticket_to_dict(ticket)), 200


@api_bp.route('/tickets/<int:ticket_id>/close', methods=['POST'])
@jwt_required()
def close_ticket(ticket_id):
    from app import db
    from models import Ticket
    user = get_current_user()
    ticket = Ticket.query.get_or_404(ticket_id)

    if user.role not in ('admin',) and ticket.created_by_id != user.id:
        return jsonify({'error': 'Access denied'}), 403

    ticket.status = 'closed'
    ticket.closed_at = datetime.utcnow()
    ticket.closed_by_id = user.id
    ticket.updated_at = datetime.utcnow()
    record_history(ticket, user, 'closed')
    db.session.commit()

    return jsonify(ticket_to_dict(ticket)), 200


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
@api_bp.route('/categories', methods=['GET'])
@jwt_required()
def list_categories():
    from models import Category
    cats = Category.query.order_by(Category.name).all()
    return jsonify([{'id': c.id, 'name': c.name, 'description': c.description} for c in cats]), 200


@api_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    from app import db
    from models import Category
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'error': 'Category name is required'}), 400

    existing = Category.query.filter_by(name=name).first()
    if existing:
        return jsonify({'error': 'Category already exists'}), 409

    cat = Category(name=name, description=description)
    db.session.add(cat)
    db.session.commit()
    return jsonify({'id': cat.id, 'name': cat.name, 'description': cat.description}), 201


# ---------------------------------------------------------------------------
# Users (Admin)
# ---------------------------------------------------------------------------
@api_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    from models import User
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    role_filter = request.args.get('role', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = User.query
    if role_filter:
        query = query.filter(User.role == role_filter)
    if search:
        query = query.filter(
            User.username.ilike(f'%{search}%') |
            User.full_name.ilike(f'%{search}%') |
            User.email.ilike(f'%{search}%')
        )
    query = query.order_by(User.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'users': [user_to_dict(u) for u in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': paginated.page,
    }), 200


@api_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    from app import db
    from models import User
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')

    if not all([username, email, full_name, password]):
        return jsonify({'error': 'username, email, full_name, password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=generate_password_hash(password),
        role=role,
        is_active=True,
        is_verified=True,
        is_approved=True,
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(user_to_dict(new_user)), 201


@api_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    from models import User
    current = get_current_user()
    if current.role != 'admin' and current.id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    user = User.query.get_or_404(user_id)
    return jsonify(user_to_dict(user)), 200


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    from app import db
    from models import User
    current = get_current_user()
    if current.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    if current.id == user_id:
        return jsonify({'error': 'Cannot delete yourself'}), 400

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'}), 200


@api_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@jwt_required()
def toggle_user_status(user_id):
    from app import db
    from models import User
    current = get_current_user()
    if current.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({'id': user.id, 'is_active': user.is_active}), 200


@api_bp.route('/users/<int:user_id>/approve', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    from app import db
    from models import User
    current = get_current_user()
    if current.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    user.is_active = True
    user.approved_by_id = current.id
    user.approved_at = datetime.utcnow()
    db.session.commit()
    return jsonify(user_to_dict(user)), 200


@api_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_user_password(user_id):
    from app import db
    from models import User
    current = get_current_user()
    if current.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    data = request.get_json(silent=True) or {}
    new_pw = data.get('new_password', '')
    if len(new_pw) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    user = User.query.get_or_404(user_id)
    user.password_hash = generate_password_hash(new_pw)
    db.session.commit()
    return jsonify({'message': 'Password reset successfully'}), 200


@api_bp.route('/users/interns/pending', methods=['GET'])
@jwt_required()
def pending_interns():
    from models import User
    current = get_current_user()
    if current.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    interns = User.query.filter_by(role='intern', is_approved=False).all()
    return jsonify([user_to_dict(u) for u in interns]), 200


@api_bp.route('/users/staff', methods=['GET'])
@jwt_required()
def list_staff():
    from models import User
    current = get_current_user()
    if current.role not in ('admin', 'intern'):
        return jsonify({'error': 'Access denied'}), 403
    staff = User.query.filter(User.role.in_(['admin', 'intern'])).order_by(User.full_name).all()
    return jsonify([user_to_dict(u) for u in staff]), 200


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@api_bp.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    from models import Notification
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    paginated = Notification.query.filter_by(user_id=user.id).order_by(
        desc(Notification.created_at)
    ).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'notifications': [notification_to_dict(n) for n in paginated.items],
        'total': paginated.total,
        'unread': Notification.query.filter_by(user_id=user.id, is_read=False).count(),
    }), 200


@api_bp.route('/notifications/unread-count', methods=['GET'])
@jwt_required()
def unread_count():
    from models import Notification
    user = get_current_user()
    count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({'count': count}), 200


@api_bp.route('/notifications/recent', methods=['GET'])
@jwt_required()
def recent_notifications():
    from models import Notification
    user = get_current_user()
    since = request.args.get('since')
    query = Notification.query.filter_by(user_id=user.id)
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(Notification.created_at > since_dt)
        except ValueError:
            pass
    items = query.order_by(desc(Notification.created_at)).limit(10).all()
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({
        'notifications': [notification_to_dict(n) for n in items],
        'unread_count': unread,
    }), 200


@api_bp.route('/notifications/<int:notif_id>/mark-read', methods=['POST'])
@jwt_required()
def mark_read(notif_id):
    from app import db
    from models import Notification
    user = get_current_user()
    n = Notification.query.filter_by(id=notif_id, user_id=user.id).first_or_404()
    n.is_read = True
    n.read_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'id': n.id, 'is_read': True}), 200


@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_read():
    from app import db
    from models import Notification
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update(
        {'is_read': True, 'read_at': datetime.utcnow()}
    )
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'}), 200


@api_bp.route('/notifications/clear-all', methods=['POST'])
@jwt_required()
def clear_all_notifications():
    from app import db
    from models import Notification
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({'message': 'All notifications cleared'}), 200


# ---------------------------------------------------------------------------
# Notification Settings
# ---------------------------------------------------------------------------
@api_bp.route('/notifications/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    from models import NotificationSettings
    user = get_current_user()
    settings = NotificationSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        return jsonify({
            'new_ticket_email': True, 'new_ticket_app': True,
            'ticket_updated_email': True, 'ticket_updated_app': True,
            'new_comment_email': True, 'new_comment_app': True,
            'ticket_closed_email': True, 'ticket_closed_app': True,
            'ticket_overdue_email': True, 'ticket_overdue_app': True,
            'do_not_disturb': False, 'dnd_start_time': None, 'dnd_end_time': None,
        }), 200
    return jsonify({
        'new_ticket_email': settings.new_ticket_email,
        'new_ticket_app': settings.new_ticket_app,
        'ticket_updated_email': settings.ticket_updated_email,
        'ticket_updated_app': settings.ticket_updated_app,
        'new_comment_email': settings.new_comment_email,
        'new_comment_app': settings.new_comment_app,
        'ticket_closed_email': settings.ticket_closed_email,
        'ticket_closed_app': settings.ticket_closed_app,
        'ticket_overdue_email': settings.ticket_overdue_email,
        'ticket_overdue_app': settings.ticket_overdue_app,
        'do_not_disturb': settings.do_not_disturb,
        'dnd_start_time': settings.dnd_start_time.strftime('%H:%M') if settings.dnd_start_time else None,
        'dnd_end_time': settings.dnd_end_time.strftime('%H:%M') if settings.dnd_end_time else None,
    }), 200


@api_bp.route('/notifications/settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    from app import db
    from models import NotificationSettings
    from datetime import time
    user = get_current_user()
    data = request.get_json(silent=True) or {}

    settings = NotificationSettings.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = NotificationSettings(user_id=user.id)
        db.session.add(settings)

    bool_fields = [
        'new_ticket_email', 'new_ticket_app',
        'ticket_updated_email', 'ticket_updated_app',
        'new_comment_email', 'new_comment_app',
        'ticket_closed_email', 'ticket_closed_app',
        'ticket_overdue_email', 'ticket_overdue_app',
        'do_not_disturb',
    ]
    for field in bool_fields:
        if field in data:
            setattr(settings, field, bool(data[field]))

    for tf in ('dnd_start_time', 'dnd_end_time'):
        if tf in data and data[tf]:
            try:
                h, m = data[tf].split(':')
                setattr(settings, tf, time(int(h), int(m)))
            except Exception:
                pass

    db.session.commit()
    return jsonify({'message': 'Settings saved'}), 200


# ---------------------------------------------------------------------------
# Reports & Analytics
# ---------------------------------------------------------------------------
@api_bp.route('/reports/stats', methods=['GET'])
@jwt_required()
def reports_stats():
    from models import Ticket, Category
    user = get_current_user()
    if user.role not in ('admin', 'intern'):
        return jsonify({'error': 'Access denied'}), 403

    start_str = request.args.get('start')
    end_str = request.args.get('end')

    query = Ticket.query
    if start_str:
        try:
            query = query.filter(Ticket.created_at >= datetime.fromisoformat(start_str))
        except ValueError:
            pass
    if end_str:
        try:
            query = query.filter(Ticket.created_at <= datetime.fromisoformat(end_str))
        except ValueError:
            pass

    total = query.count()
    open_t = query.filter(Ticket.status == 'open').count()
    in_progress = query.filter(Ticket.status == 'in_progress').count()
    resolved = query.filter(Ticket.status == 'resolved').count()
    closed = query.filter(Ticket.status == 'closed').count()
    escalated = query.filter(Ticket.status == 'escalated').count()

    # By category
    by_category = []
    cats = Category.query.all()
    for c in cats:
        cnt = query.filter(Ticket.category_id == c.id).count()
        if cnt > 0:
            by_category.append({'category': c.name, 'count': cnt})

    # By priority
    by_priority = []
    for p in ('low', 'medium', 'high', 'urgent'):
        cnt = query.filter(Ticket.priority == p).count()
        by_priority.append({'priority': p, 'count': cnt})

    # Daily volume (last 30 days)
    daily = []
    for i in range(29, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        cnt = Ticket.query.filter(Ticket.created_at >= day_start, Ticket.created_at <= day_end).count()
        daily.append({'date': day.isoformat(), 'count': cnt})

    return jsonify({
        'total': total,
        'open': open_t,
        'in_progress': in_progress,
        'resolved': resolved,
        'closed': closed,
        'escalated': escalated,
        'by_category': by_category,
        'by_priority': by_priority,
        'daily_volume': daily,
    }), 200


@api_bp.route('/analytics/stats', methods=['GET'])
@jwt_required()
def analytics_stats():
    from models import Ticket, User
    user = get_current_user()
    if user.role != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    total = Ticket.query.count()
    resolved = Ticket.query.filter(Ticket.status.in_(['resolved', 'closed'])).count()
    sla_compliance = round((resolved / total * 100), 1) if total > 0 else 0

    # Tickets by assignee
    from sqlalchemy import text
    assignee_load = []
    staff = User.query.filter(User.role.in_(['admin', 'intern'])).all()
    for s in staff:
        cnt = len(s.assigned_tickets)
        if cnt > 0:
            assignee_load.append({'name': s.full_name, 'count': cnt})
    assignee_load.sort(key=lambda x: x['count'], reverse=True)

    return jsonify({
        'total_tickets': total,
        'resolved_tickets': resolved,
        'sla_compliance': sla_compliance,
        'assignee_workload': assignee_load[:10],
    }), 200


# ---------------------------------------------------------------------------
# File serving
# ---------------------------------------------------------------------------
@api_bp.route('/attachments/<path:filename>', methods=['GET'])
@jwt_required()
def serve_attachment(filename):
    from app import app
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
