from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import Student, Staff, Book, BorrowRecord, Fine, db
from sqlalchemy import func
from utils.email_service import send_due_date_reminders, send_overdue_notices, get_email_statistics
import os

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Get dashboard statistics
    total_students = Student.query.count()
    total_staff = Staff.query.count()
    total_books = Book.query.count()
    active_borrows = BorrowRecord.query.filter_by(returned_at=None).count()
    total_fines = db.session.query(func.sum(Fine.amount)).filter_by(paid=False).scalar() or 0
    
    # Get recent activities
    recent_borrows = BorrowRecord.query.order_by(BorrowRecord.borrowed_at.desc()).limit(5).all()
    overdue_books = BorrowRecord.query.filter(
        BorrowRecord.returned_at.is_(None),
        BorrowRecord.due_date < func.now()
    ).all()
    
    # Get email statistics
    email_stats = get_email_statistics()
    
    # Check if SendGrid API key is configured
    has_sendgrid = bool(os.environ.get('SENDGRID_API_KEY'))
    
    return render_template('dashboard/index.html',
                         total_students=total_students,
                         total_staff=total_staff,
                         total_books=total_books,
                         active_borrows=active_borrows,
                         total_fines=total_fines,
                         recent_borrows=recent_borrows,
                         overdue_books=overdue_books,
                         email_stats=email_stats,
                         has_sendgrid=has_sendgrid)

@dashboard_bp.route('/send-due-reminders')
@login_required
def send_due_reminders():
    """Manually trigger due date reminder emails"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    sent_count = send_due_date_reminders()
    flash(f'Successfully sent {sent_count} due date reminder emails.', 'success')
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/send-overdue-notices')
@login_required
def send_overdue_notices_route():
    """Manually trigger overdue notice emails"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    sent_count = send_overdue_notices()
    flash(f'Successfully sent {sent_count} overdue notice emails.', 'success')
    return redirect(url_for('dashboard.index'))