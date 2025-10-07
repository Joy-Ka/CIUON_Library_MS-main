import os
import sqlite3
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import BackupLog, db
from utils.audit_logger import log_action

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/')
@login_required
def list_backups():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    backups = BackupLog.query.order_by(BackupLog.created_at.desc()).all()
    
    # Check if backup directory exists
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    return render_template('backup/list.html', backups=backups)

@backup_bp.route('/create', methods=['POST'])
@login_required
def create_backup():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('backup.list_backups'))
    
    try:
        # Create backup directory if it doesn't exist
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Generate backup filename with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'library_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create backup of SQLite database
        source_db = 'confucius_library.db'
        
        if os.path.exists(source_db):
            # Use SQLite backup API for consistency
            source_conn = sqlite3.connect(source_db)
            backup_conn = sqlite3.connect(backup_path)
            
            source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Get file size
            file_size = os.path.getsize(backup_path)
            
            # Create backup log entry
            description = request.form.get('description', f'Manual backup created by {current_user.username}')
            
            backup_log = BackupLog(
                filename=backup_filename,
                created_by=current_user.id,
                file_size=file_size,
                description=description,
                status='completed'
            )
            
            db.session.add(backup_log)
            db.session.commit()
            
            # Log the action
            log_action(
                action='CREATE_BACKUP',
                entity_type='Backup',
                entity_id=backup_log.id,
                details={
                    'filename': backup_filename,
                    'file_size': file_size,
                    'description': description
                }
            )
            
            flash(f'Backup created successfully: {backup_filename}', 'success')
            
        else:
            flash('Database file not found', 'error')
            
    except Exception as e:
        # Log failed backup
        backup_log = BackupLog(
            filename=f'failed_backup_{timestamp}.db',
            created_by=current_user.id,
            status='failed',
            description=f'Backup failed: {str(e)}'
        )
        
        db.session.add(backup_log)
        db.session.commit()
        
        flash(f'Backup failed: {str(e)}', 'error')
    
    return redirect(url_for('backup.list_backups'))

@backup_bp.route('/download/<int:backup_id>')
@login_required
def download_backup(backup_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('backup.list_backups'))
    
    backup_log = BackupLog.query.get_or_404(backup_id)
    backup_path = os.path.join('backups', backup_log.filename)
    
    if os.path.exists(backup_path):
        log_action(
            action='DOWNLOAD_BACKUP',
            entity_type='Backup',
            entity_id=backup_id,
            details={
                'filename': backup_log.filename
            }
        )
        
        return send_file(backup_path, as_attachment=True, download_name=backup_log.filename)
    else:
        flash('Backup file not found', 'error')
        return redirect(url_for('backup.list_backups'))

@backup_bp.route('/restore/<int:backup_id>', methods=['POST'])
@login_required
def restore_backup(backup_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('backup.list_backups'))
    
    backup_log = BackupLog.query.get_or_404(backup_id)
    backup_path = os.path.join('backups', backup_log.filename)
    
    if not os.path.exists(backup_path):
        flash('Backup file not found', 'error')
        return redirect(url_for('backup.list_backups'))
    
    try:
        # Create a backup of current database before restoring
        current_timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        pre_restore_backup = f'pre_restore_backup_{current_timestamp}.db'
        pre_restore_path = os.path.join('backups', pre_restore_backup)
        
        source_db = 'confucius_library.db'
        if os.path.exists(source_db):
            shutil.copy2(source_db, pre_restore_path)
        
        # Restore from backup
        shutil.copy2(backup_path, source_db)
        
        # Log the restoration
        log_action(
            action='RESTORE_BACKUP',
            entity_type='Backup',
            entity_id=backup_id,
            details={
                'restored_from': backup_log.filename,
                'pre_restore_backup': pre_restore_backup
            }
        )
        
        flash(f'Database restored from {backup_log.filename}', 'success')
        flash(f'Pre-restoration backup saved as {pre_restore_backup}', 'info')
        
    except Exception as e:
        flash(f'Restore failed: {str(e)}', 'error')
    
    return redirect(url_for('backup.list_backups'))

@backup_bp.route('/delete/<int:backup_id>', methods=['POST'])
@login_required
def delete_backup(backup_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('backup.list_backups'))
    
    backup_log = BackupLog.query.get_or_404(backup_id)
    backup_path = os.path.join('backups', backup_log.filename)
    
    try:
        # Delete the backup file
        if os.path.exists(backup_path):
            os.remove(backup_path)
        
        # Log the deletion
        log_action(
            action='DELETE_BACKUP',
            entity_type='Backup',
            entity_id=backup_id,
            details={
                'filename': backup_log.filename
            }
        )
        
        # Remove from database
        db.session.delete(backup_log)
        db.session.commit()
        
        flash(f'Backup {backup_log.filename} deleted successfully', 'success')
        
    except Exception as e:
        flash(f'Failed to delete backup: {str(e)}', 'error')
    
    return redirect(url_for('backup.list_backups'))