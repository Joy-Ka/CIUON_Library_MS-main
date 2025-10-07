from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

# Create SQLAlchemy instance that will be initialized in app.py
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='librarian')  # admin, librarian
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)  # Renamed from is_active to avoid conflict

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    books = db.relationship('Book', backref='category_ref', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(50), unique=True, nullable=True)  # UoN students
    id_number = db.Column(db.String(20), unique=True, nullable=True)  # Kenyan non-UoN
    passport_number = db.Column(db.String(20), unique=True, nullable=True)  # International
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    membership_status = db.Column(db.String(20), default='active')  # active, suspended, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    borrow_records = db.relationship('BorrowRecord', backref='student_ref', lazy=True)
    fines = db.relationship('Fine', backref='student_ref', lazy=True)
    
    @property
    def identifier(self):
        """Return the primary identifier for the student"""
        if self.registration_number:
            return self.registration_number
        elif self.id_number:
            return self.id_number
        else:
            return self.passport_number
    
    @property
    def current_borrowed_count(self):
        """Get current number of borrowed books"""
        return BorrowRecord.query.filter_by(student_id=self.id, returned_at=None).count()
    
    @property
    def total_fines(self):
        """Get total unpaid fines"""
        return sum(fine.amount for fine in self.fines if not fine.paid)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    staff_type = db.Column(db.String(20), nullable=False)  # teacher, intern
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    borrow_records = db.relationship('BorrowRecord', backref='staff_ref', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200))
    publisher = db.Column(db.String(200))
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    total_copies = db.Column(db.Integer, default=1)
    shelf_location = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    borrow_records = db.relationship('BorrowRecord', backref='book_ref', lazy=True)
    
    @property
    def available_copies(self):
        """Get number of available copies"""
        borrowed_count = BorrowRecord.query.filter_by(book_id=self.id, returned_at=None).count()
        return self.total_copies - borrowed_count
    
    @property
    def category_name(self):
        """Get category name or 'Uncategorized'"""
        return self.category_ref.name if self.category_ref else 'Uncategorized'

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    borrowed_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(BorrowRecord, self).__init__(**kwargs)
        if not self.due_date:
            # Students get 3 days, staff gets 30 days default
            if self.student_id:
                self.due_date = datetime.utcnow() + timedelta(days=3)
            else:
                self.due_date = datetime.utcnow() + timedelta(days=30)
    
    @property
    def is_overdue(self):
        """Check if the book is overdue"""
        return not self.returned_at and datetime.utcnow() > self.due_date
    
    @property
    def days_overdue(self):
        """Get number of days overdue"""
        if self.is_overdue:
            return (datetime.utcnow() - self.due_date).days
        return 0
    
    @property
    def borrower_name(self):
        """Get borrower name (student or staff)"""
        if self.student_ref:
            return self.student_ref.name
        elif self.staff_ref:
            return self.staff_ref.name
        return "Unknown"
    
    @property
    def borrower_type(self):
        """Get borrower type"""
        return "Student" if self.student_id else "Staff"

class Fine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    borrow_record_id = db.Column(db.Integer, db.ForeignKey('borrow_record.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Amount in KES
    original_amount = db.Column(db.Float, nullable=True)  # Original fine amount before adjustments
    reason = db.Column(db.String(200), default='Late return')
    paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime, nullable=True)
    waived = db.Column(db.Boolean, default=False)
    waived_at = db.Column(db.DateTime, nullable=True)
    waived_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    waiver_reason = db.Column(db.Text, nullable=True)
    adjustment_amount = db.Column(db.Float, default=0.0)  # Amount adjusted (positive or negative)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Fine, self).__init__(**kwargs)
        # Set original_amount to amount if not specified
        if self.original_amount is None and self.amount is not None:
            self.original_amount = self.amount
    
    # Relationships
    borrow_record = db.relationship('BorrowRecord', backref='fine_ref', lazy=True)
    waived_by_user = db.relationship('User', backref='waived_fines', lazy=True)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # e.g., 'CREATE_STUDENT', 'BORROW_BOOK', 'WAIVE_FINE'
    entity_type = db.Column(db.String(50), nullable=False)  # e.g., 'Student', 'Book', 'BorrowRecord'
    entity_id = db.Column(db.Integer, nullable=True)  # ID of the affected entity
    details = db.Column(db.Text, nullable=True)  # JSON string with action details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # User's IP address
    
    # Relationships
    user = db.relationship('User', backref='audit_logs', lazy=True)

class BackupLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    status = db.Column(db.String(20), default='completed')  # completed, failed, in_progress
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    created_by_user = db.relationship('User', backref='backups_created', lazy=True)

class NotificationPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    email_due_reminder = db.Column(db.Boolean, default=True)  # Email reminder before due date
    email_overdue_notice = db.Column(db.Boolean, default=True)  # Email when overdue
    days_before_due = db.Column(db.Integer, default=1)  # Days before due date to send reminder
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='notification_preferences', lazy=True)

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    email_type = db.Column(db.String(50), nullable=False)  # 'due_reminder', 'overdue_notice'
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    borrow_record_id = db.Column(db.Integer, db.ForeignKey('borrow_record.id'), nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='sent')  # sent, failed, pending
    error_message = db.Column(db.Text, nullable=True)
    
    # Relationships
    student = db.relationship('Student', backref='emails_received', lazy=True)
    borrow_record = db.relationship('BorrowRecord', backref='emails_sent', lazy=True)