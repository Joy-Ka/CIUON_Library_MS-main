from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Student, Staff, Book, BorrowRecord, Fine, db
from sqlalchemy import func

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
    
    return render_template('dashboard/index.html',
                         total_students=total_students,
                         total_staff=total_staff,
                         total_books=total_books,
                         active_borrows=active_borrows,
                         total_fines=total_fines,
                         recent_borrows=recent_borrows,
                         overdue_books=overdue_books)