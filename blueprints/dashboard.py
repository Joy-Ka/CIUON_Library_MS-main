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
    
    # Check if email service is configured
    has_gmail = bool(os.environ.get('GMAIL_USER') and os.environ.get('GMAIL_APP_PASSWORD'))
    has_sendgrid = bool(os.environ.get('SENDGRID_API_KEY'))
    has_email_service = has_gmail or has_sendgrid
    
    return render_template('dashboard/index.html',
                         total_students=total_students,
                         total_staff=total_staff,
                         total_books=total_books,
                         active_borrows=active_borrows,
                         total_fines=total_fines,
                         recent_borrows=recent_borrows,
                         overdue_books=overdue_books,
                         email_stats=email_stats,
                         has_email_service=has_email_service,
                         has_gmail=has_gmail,
                         has_sendgrid=has_sendgrid)

@dashboard_bp.route('/send-due-reminders')
@login_required


@dashboard_bp.route('/test-email')
@login_required
def test_email():
    """Send a test email to verify configuration"""
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Import here to avoid circular imports
    from utils.email_service import send_email
    
    # Send test email to admin
    test_email = current_user.email
    subject = "Library System - Email Test"
    body = """
This is a test email from the Confucius Institute Library Management System.

If you received this email, your email configuration is working correctly!

System Information:
- Sent at: """ + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC') + """
- User: """ + current_user.username + """

Best regards,
Library System
"""
    
    if send_email(test_email, subject, body, 'test', None, None):
        flash(f'Test email sent successfully to {test_email}. Check your inbox!', 'success')
    else:
        flash('Failed to send test email. Check email configuration in Secrets.', 'error')
    
    return redirect(url_for('dashboard.index'))

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