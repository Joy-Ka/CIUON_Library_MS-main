from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models import Book, Student, Staff, BorrowRecord, Fine, Category, db
from sqlalchemy import func, desc
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    # Only admin can access reports
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    return render_template('reports/index.html')

@reports_bp.route('/most-borrowed')
@login_required
def most_borrowed_books():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get most borrowed books
    most_borrowed = db.session.query(
        Book.title,
        Book.author,
        Book.unique_id,
        func.count(BorrowRecord.id).label('borrow_count')
    ).join(BorrowRecord).group_by(Book.id).order_by(desc('borrow_count')).limit(20).all()
    
    return render_template('reports/most_borrowed.html', books=most_borrowed)

@reports_bp.route('/active-students')
@login_required
def active_students():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get most active students
    active_students = db.session.query(
        Student.name,
        Student.identifier,
        func.count(BorrowRecord.id).label('borrow_count')
    ).join(BorrowRecord).group_by(Student.id).order_by(desc('borrow_count')).limit(20).all()
    
    return render_template('reports/active_students.html', students=active_students)

@reports_bp.route('/category-trends')
@login_required
def category_trends():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get borrowing trends by category
    category_stats = db.session.query(
        Category.name,
        func.count(BorrowRecord.id).label('borrow_count'),
        func.count(Book.id).label('total_books')
    ).join(Book).outerjoin(BorrowRecord).group_by(Category.id).all()
    
    # Include uncategorized books
    uncategorized_books = Book.query.filter_by(category_id=None).count()
    uncategorized_borrows = db.session.query(func.count(BorrowRecord.id)).join(Book).filter(Book.category_id.is_(None)).scalar()
    
    if uncategorized_books > 0:
        category_stats.append(('Uncategorized', uncategorized_borrows or 0, uncategorized_books))
    
    return render_template('reports/category_trends.html', categories=category_stats)

@reports_bp.route('/stock-status')
@login_required
def stock_status():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get stock information for all books
    books = Book.query.all()
    stock_data = []
    
    for book in books:
        stock_data.append({
            'title': book.title,
            'author': book.author,
            'unique_id': book.unique_id,
            'category': book.category_name,
            'total_copies': book.total_copies,
            'available_copies': book.available_copies,
            'borrowed_copies': book.total_copies - book.available_copies
        })
    
    return render_template('reports/stock_status.html', books=stock_data)

@reports_bp.route('/overdue-items')
@login_required
def overdue_items():
    # Get overdue items (students only have fines)
    overdue_borrows = BorrowRecord.query.filter(
        BorrowRecord.returned_at.is_(None),
        BorrowRecord.due_date < func.now()
    ).all()
    
    return render_template('reports/overdue_items.html', overdue_borrows=overdue_borrows)

@reports_bp.route('/staff-borrows')
@login_required
def staff_borrows():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get all staff borrow records
    staff_borrows = BorrowRecord.query.filter(BorrowRecord.staff_id.isnot(None)).order_by(BorrowRecord.borrowed_at.desc()).all()
    
    return render_template('reports/staff_borrows.html', staff_borrows=staff_borrows)

@reports_bp.route('/stock-depletion')
@login_required
def stock_depletion():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Get books with low stock (less than 2 available copies)
    low_stock_books = []
    books = Book.query.all()
    
    for book in books:
        if book.available_copies <= 1:
            low_stock_books.append({
                'title': book.title,
                'author': book.author,
                'unique_id': book.unique_id,
                'category': book.category_name,
                'total_copies': book.total_copies,
                'available_copies': book.available_copies,
                'borrowed_copies': book.total_copies - book.available_copies
            })
    
    return render_template('reports/stock_depletion.html', low_stock_books=low_stock_books)

@reports_bp.route('/inactive-students')
@login_required
def inactive_students():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Students with no borrowing activity in the last 6 months
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Get students who have never borrowed or haven't borrowed in 6 months
    inactive_students = db.session.query(Student).outerjoin(BorrowRecord).group_by(Student.id).having(
        func.max(BorrowRecord.borrowed_at) < six_months_ago or func.max(BorrowRecord.borrowed_at).is_(None)
    ).all()
    
    return render_template('reports/inactive_students.html', 
                         inactive_students=inactive_students,
                         months_threshold=6)

@reports_bp.route('/charts-data')
@login_required
def charts_data():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    # Borrowing trends by month (last 12 months)
    one_year_ago = datetime.utcnow() - timedelta(days=365)
    monthly_borrows = db.session.query(
        func.strftime('%Y-%m', BorrowRecord.borrowed_at).label('month'),
        func.count(BorrowRecord.id).label('count')
    ).filter(BorrowRecord.borrowed_at >= one_year_ago).group_by('month').all()
    
    # Category distribution
    category_distribution = db.session.query(
        Category.name,
        func.count(BorrowRecord.id).label('borrow_count')
    ).join(Book).join(BorrowRecord).group_by(Category.id).all()
    
    # Include uncategorized books
    uncategorized_borrows = db.session.query(
        func.count(BorrowRecord.id)
    ).join(Book).filter(Book.category_id.is_(None)).scalar() or 0
    
    if uncategorized_borrows > 0:
        category_distribution = list(category_distribution) + [('Uncategorized', uncategorized_borrows)]
    
    # Fine collection trends (last 12 months)
    fine_trends = db.session.query(
        func.strftime('%Y-%m', Fine.created_at).label('month'),
        func.sum(Fine.amount).label('total_amount'),
        func.count(Fine.id).label('fine_count')
    ).filter(
        Fine.created_at >= one_year_ago,
        Fine.paid == True
    ).group_by('month').all()
    
    # Student vs Staff borrowing ratio
    student_borrows = BorrowRecord.query.filter(BorrowRecord.student_id.isnot(None)).count()
    staff_borrows = BorrowRecord.query.filter(BorrowRecord.staff_id.isnot(None)).count()
    
    return jsonify({
        'monthly_borrows': [{'month': item[0], 'count': item[1]} for item in monthly_borrows],
        'category_distribution': [{'category': item[0], 'count': item[1]} for item in category_distribution],
        'fine_trends': [{'month': item[0], 'amount': float(item[1]), 'count': item[2]} for item in fine_trends],
        'borrower_ratio': {
            'students': student_borrows,
            'staff': staff_borrows
        }
    })

@reports_bp.route('/charts')
@login_required
def charts():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    return render_template('reports/charts.html')