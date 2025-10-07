import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import current_app
from models import EmailLog, NotificationPreference, BorrowRecord, Student, db
from utils.audit_logger import log_action

# Email service configuration
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
FROM_EMAIL = os.environ.get('FROM_EMAIL', GMAIL_USER or 'library@confucius.uonbi.ac.ke')

def send_email(to_email, subject, body, email_type, student_id=None, borrow_record_id=None):
    """
    Send an email using Gmail SMTP or SendGrid and log it
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
        email_type (str): Type of email ('due_reminder', 'overdue_notice')
        student_id (int): Student ID if applicable
        borrow_record_id (int): Borrow record ID if applicable
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        status = 'sent'
        error_message = None
        
        # Try Gmail SMTP first if credentials are available
        if GMAIL_USER and GMAIL_APP_PASSWORD:
            try:
                msg = MIMEMultipart()
                msg['From'] = GMAIL_USER
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                # Connect to Gmail SMTP server
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                    server.send_message(msg)
                
                current_app.logger.info(f"Email sent successfully via Gmail to {to_email}")
                status = 'sent'
                error_message = None
            except Exception as gmail_error:
                current_app.logger.error(f"Gmail SMTP error: {str(gmail_error)}")
                status = 'failed'
                error_message = f'Gmail SMTP error: {str(gmail_error)}'
        
        # Try SendGrid if Gmail failed or not configured
        elif SENDGRID_API_KEY:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
            
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body
            )
            
            response = sg.send(message)
            
            # Check if send was successful
            if response.status_code >= 200 and response.status_code < 300:
                status = 'sent'
                error_message = None
            else:
                status = 'failed'
                error_message = f'SendGrid error: {response.status_code}'
        else:
            # No email credentials configured
            current_app.logger.warning(f"Email NOT SENT (no credentials) - To: {to_email}, Subject: {subject}")
            status = 'failed'
            error_message = 'No email credentials configured (GMAIL_USER or SENDGRID_API_KEY required)'
        
        # Log the email
        email_log = EmailLog(
            recipient_email=to_email,
            subject=subject,
            body=body,
            email_type=email_type,
            student_id=student_id,
            borrow_record_id=borrow_record_id,
            status=status,
            error_message=error_message
        )
        
        db.session.add(email_log)
        db.session.commit()
        
        # Log action in audit trail
        log_action(
            action='SEND_EMAIL',
            entity_type='Email',
            entity_id=email_log.id,
            details={
                'recipient': to_email,
                'subject': subject,
                'email_type': email_type,
                'student_id': student_id,
                'borrow_record_id': borrow_record_id,
                'status': status
            }
        )
        
        return status == 'sent'
        
    except Exception as e:
        # Log failed email
        email_log = EmailLog(
            recipient_email=to_email,
            subject=subject,
            body=body,
            email_type=email_type,
            student_id=student_id,
            borrow_record_id=borrow_record_id,
            status='failed',
            error_message=str(e)
        )
        
        db.session.add(email_log)
        db.session.commit()
        
        current_app.logger.error(f"Failed to send email: {e}")
        return False

def send_due_date_reminders():
    """
    Send due date reminder emails to students
    """
    # Get borrowing records that are due in 1-2 days (configurable per student)
    tomorrow = datetime.utcnow() + timedelta(days=1)
    day_after_tomorrow = datetime.utcnow() + timedelta(days=2)
    
    # Get active borrows due soon
    upcoming_due_borrows = BorrowRecord.query.filter(
        BorrowRecord.returned_at.is_(None),
        BorrowRecord.due_date >= tomorrow,
        BorrowRecord.due_date <= day_after_tomorrow,
        BorrowRecord.student_id.isnot(None)  # Only students, not staff
    ).all()
    
    sent_count = 0
    
    for borrow in upcoming_due_borrows:
        student = borrow.student_ref
        
        # Check if student has notification preferences
        prefs = NotificationPreference.query.filter_by(student_id=student.id).first()
        
        # Default to sending reminders if no preferences set
        if not prefs or prefs.email_due_reminder:
            days_until_due = (borrow.due_date.date() - datetime.utcnow().date()).days
            
            # Check if we should send reminder based on preference
            days_before = prefs.days_before_due if prefs else 1
            
            if days_until_due <= days_before:
                subject = f"Library Book Due Reminder - {borrow.book_ref.title}"
                body = f"""
Dear {student.name},

This is a friendly reminder that you have a book due soon:

Book: {borrow.book_ref.title}
Author: {borrow.book_ref.author or 'N/A'}
Due Date: {borrow.due_date.strftime('%B %d, %Y')}
Days Until Due: {days_until_due}

Please return the book on time to avoid late fees.

Thank you,
Confucius Institute Library
University of Nairobi
"""
                
                if send_email(student.email, subject, body, 'due_reminder', student.id, borrow.id):
                    sent_count += 1
    
    return sent_count

def send_overdue_notices():
    """
    Send overdue notices to students
    """
    # Get overdue borrows
    overdue_borrows = BorrowRecord.query.filter(
        BorrowRecord.returned_at.is_(None),
        BorrowRecord.due_date < datetime.utcnow(),
        BorrowRecord.student_id.isnot(None)  # Only students, not staff
    ).all()
    
    sent_count = 0
    
    for borrow in overdue_borrows:
        student = borrow.student_ref
        
        # Check if student has notification preferences
        prefs = NotificationPreference.query.filter_by(student_id=student.id).first()
        
        # Default to sending overdue notices if no preferences set
        if not prefs or prefs.email_overdue_notice:
            days_overdue = borrow.days_overdue
            fine_amount = days_overdue * 20  # 20 KES per day
            
            subject = f"OVERDUE NOTICE - {borrow.book_ref.title}"
            body = f"""
Dear {student.name},

This is an overdue notice for the following book:

Book: {borrow.book_ref.title}
Author: {borrow.book_ref.author or 'N/A'}
Due Date: {borrow.due_date.strftime('%B %d, %Y')}
Days Overdue: {days_overdue}
Fine Amount: KES {fine_amount}

Please return the book immediately to avoid additional charges.

Contact the library if you need assistance.

Confucius Institute Library
University of Nairobi
Phone: [Library Phone Number]
Email: library@confucius.uonbi.ac.ke
"""
            
            if send_email(student.email, subject, body, 'overdue_notice', student.id, borrow.id):
                sent_count += 1
    
    return sent_count

def get_email_statistics():
    """
    Get email sending statistics
    """
    total_sent = EmailLog.query.filter_by(status='sent').count()
    total_failed = EmailLog.query.filter_by(status='failed').count()
    
    due_reminders = EmailLog.query.filter_by(email_type='due_reminder', status='sent').count()
    overdue_notices = EmailLog.query.filter_by(email_type='overdue_notice', status='sent').count()
    
    return {
        'total_sent': total_sent,
        'total_failed': total_failed,
        'due_reminders': due_reminders,
        'overdue_notices': overdue_notices
    }