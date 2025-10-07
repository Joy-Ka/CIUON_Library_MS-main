import json
from flask import request
from flask_login import current_user
from models import AuditLog, db
from datetime import datetime

def log_action(action, entity_type, entity_id=None, details=None, user_id=None):
    """
    Log an action to the audit trail
    
    Args:
        action (str): Action performed (e.g., 'CREATE_STUDENT', 'BORROW_BOOK')
        entity_type (str): Type of entity affected (e.g., 'Student', 'Book')
        entity_id (int): ID of the affected entity
        details (dict): Additional details about the action
        user_id (int): User who performed the action (defaults to current_user)
    """
    try:
        # Get user ID
        if user_id is None:
            user_id = current_user.id if current_user.is_authenticated else None
        
        # Get client IP address
        ip_address = None
        if request:
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
        
        # Convert details to JSON string
        details_json = None
        if details:
            details_json = json.dumps(details, default=str)
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details_json,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
    except Exception as e:
        # Don't let audit logging break the main application
        print(f"Audit logging failed: {e}")
        db.session.rollback()

def get_audit_logs(limit=100, entity_type=None, action=None, user_id=None):
    """
    Retrieve audit logs with optional filtering
    
    Args:
        limit (int): Maximum number of logs to retrieve
        entity_type (str): Filter by entity type
        action (str): Filter by action
        user_id (int): Filter by user ID
    
    Returns:
        List of AuditLog objects
    """
    query = AuditLog.query
    
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

def get_entity_history(entity_type, entity_id):
    """
    Get audit history for a specific entity
    
    Args:
        entity_type (str): Type of entity
        entity_id (int): ID of the entity
    
    Returns:
        List of AuditLog objects for the entity
    """
    return AuditLog.query.filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(AuditLog.timestamp.desc()).all()