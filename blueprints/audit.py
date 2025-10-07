from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import AuditLog, User, db
from utils.audit_logger import get_audit_logs, get_entity_history
import json

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/')
@login_required
def list_audit_logs():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get filters from request
    entity_type = request.args.get('entity_type', '')
    action = request.args.get('action', '')
    user_id = request.args.get('user_id', '')
    limit = int(request.args.get('limit', 100))
    
    # Apply filters
    query = AuditLog.query
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user_id:
        query = query.filter(AuditLog.user_id == int(user_id))
    
    # Get paginated results
    page = request.args.get('page', 1, type=int)
    per_page = min(limit, 100)  # Maximum 100 per page
    
    audit_logs = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique entity types and actions for filter dropdowns
    entity_types = db.session.query(AuditLog.entity_type.distinct()).all()
    entity_types = [et[0] for et in entity_types]
    
    actions = db.session.query(AuditLog.action.distinct()).all()
    actions = [a[0] for a in actions]
    
    users = User.query.all()
    
    return render_template('audit/list.html', 
                         audit_logs=audit_logs,
                         entity_types=entity_types,
                         actions=actions,
                         users=users,
                         filters={
                             'entity_type': entity_type,
                             'action': action,
                             'user_id': user_id,
                             'limit': limit
                         })

@audit_bp.route('/entity/<entity_type>/<int:entity_id>')
@login_required
def entity_history(entity_type, entity_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get entity history
    history = get_entity_history(entity_type, entity_id)
    
    return render_template('audit/entity_history.html', 
                         history=history,
                         entity_type=entity_type,
                         entity_id=entity_id)

@audit_bp.route('/details/<int:log_id>')
@login_required
def log_details(log_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    audit_log = AuditLog.query.get_or_404(log_id)
    
    # Parse details JSON
    details = {}
    if audit_log.details:
        try:
            details = json.loads(audit_log.details)
        except:
            details = {'raw': audit_log.details}
    
    return jsonify({
        'id': audit_log.id,
        'user': audit_log.user.username if audit_log.user else 'System',
        'action': audit_log.action,
        'entity_type': audit_log.entity_type,
        'entity_id': audit_log.entity_id,
        'timestamp': audit_log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': audit_log.ip_address,
        'details': details
    })

@audit_bp.route('/statistics')
@login_required
def audit_statistics():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get audit statistics
    total_logs = AuditLog.query.count()
    
    # Actions by type
    action_stats = db.session.query(
        AuditLog.action,
        db.func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(db.func.count(AuditLog.id).desc()).all()
    
    # Entity types by frequency
    entity_stats = db.session.query(
        AuditLog.entity_type,
        db.func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.entity_type).order_by(db.func.count(AuditLog.id).desc()).all()
    
    # User activity
    user_stats = db.session.query(
        User.username,
        db.func.count(AuditLog.id).label('count')
    ).join(AuditLog).group_by(User.id).order_by(db.func.count(AuditLog.id).desc()).limit(10).all()
    
    # Recent activity (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_activity = AuditLog.query.filter(AuditLog.timestamp >= yesterday).count()
    
    return render_template('audit/statistics.html',
                         total_logs=total_logs,
                         action_stats=action_stats,
                         entity_stats=entity_stats,
                         user_stats=user_stats,
                         recent_activity=recent_activity)