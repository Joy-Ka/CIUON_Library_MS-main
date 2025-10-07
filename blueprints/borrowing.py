from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Book, Student, Staff, BorrowRecord, Fine, db
from datetime import datetime, timedelta
from utils.audit_logger import log_action

borrowing_bp = Blueprint('borrowing', __name__)

@borrowing_bp.route('/')
@login_required
def list_borrows():
    status = request.args.get('status', 'active')
    
    if status == 'active':
        borrows = BorrowRecord.query.filter_by(returned_at=None).order_by(BorrowRecord.borrowed_at.desc()).all()
    elif status == 'returned':
        borrows = BorrowRecord.query.filter(BorrowRecord.returned_at.isnot(None)).order_by(BorrowRecord.returned_at.desc()).all()
    elif status == 'overdue':
        borrows = BorrowRecord.query.filter(
            BorrowRecord.returned_at.is_(None),
            BorrowRecord.due_date < datetime.utcnow()
        ).all()
    else:
        borrows = BorrowRecord.query.order_by(BorrowRecord.borrowed_at.desc()).all()
    
    return render_template('borrowing/list.html', borrows=borrows, status=status)

@borrowing_bp.route('/borrow', methods=['GET', 'POST'])
@login_required
def borrow_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        borrower_type = request.form['borrower_type']
        student_id = request.form.get('student_id') if borrower_type == 'student' else None
        staff_id = request.form.get('staff_id') if borrower_type == 'staff' else None
        
        book = Book.query.get_or_404(book_id)
        
        # Check availability
        if book.available_copies <= 0:
            flash('This book is not available for borrowing', 'error')
            students = Student.query.order_by(Student.name).all()
            staff = Staff.query.order_by(Staff.name).all()
            books = Book.query.filter(Book.available_copies > 0).order_by(Book.title).all()
            return render_template('borrowing/borrow_form.html', students=students, staff=staff, books=books)
        
        # Check student borrowing limits
        if student_id:
            student = Student.query.get_or_404(student_id)
            if student.current_borrowed_count >= 3:
                flash('Student has reached the maximum borrowing limit of 3 books', 'error')
                students = Student.query.order_by(Student.name).all()
                staff = Staff.query.order_by(Staff.name).all()
                books = Book.query.filter(Book.available_copies > 0).order_by(Book.title).all()
                return render_template('borrowing/borrow_form.html', students=students, staff=staff, books=books)
        
        # Create borrow record
        borrow_record = BorrowRecord(
            book_id=book_id,
            student_id=student_id,
            staff_id=staff_id,
            notes=request.form.get('notes', '')
        )
        
        try:
            db.session.add(borrow_record)
            db.session.commit()
            
            borrower_name = student.name if student_id else Staff.query.get(staff_id).name
            
            # Log the action
            log_action(
                action='BORROW_BOOK',
                entity_type='BorrowRecord',
                entity_id=borrow_record.id,
                details={
                    'book_id': book_id,
                    'book_title': book.title,
                    'borrower_type': 'Student' if student_id else 'Staff',
                    'borrower_id': student_id or staff_id,
                    'borrower_name': borrower_name,
                    'due_date': borrow_record.due_date.isoformat()
                }
            )
            
            flash(f'Book "{book.title}" successfully borrowed by {borrower_name}', 'success')
            return redirect(url_for('borrowing.list_borrows'))
        except Exception as e:
            db.session.rollback()
            flash('Error processing borrow request', 'error')
    
    # GET request - load data for dropdowns
    students = Student.query.order_by(Student.name).all()
    staff = Staff.query.order_by(Staff.name).all()
    books = Book.query.filter(Book.available_copies > 0).order_by(Book.title).all()
    
    return render_template('borrowing/borrow_form.html', students=students, staff=staff, books=books)

@borrowing_bp.route('/return/<int:borrow_id>', methods=['GET', 'POST'])
@login_required
def return_book(borrow_id):
    borrow_record = BorrowRecord.query.get_or_404(borrow_id)
    
    if borrow_record.returned_at:
        flash('This book has already been returned', 'error')
        return redirect(url_for('borrowing.list_borrows'))
    
    if request.method == 'POST':
        borrow_record.returned_at = datetime.utcnow()
        borrow_record.notes = request.form.get('notes', borrow_record.notes)
        
        # Calculate fine for students if overdue
        if borrow_record.student_id and borrow_record.is_overdue:
            days_overdue = borrow_record.days_overdue
            fine_amount = days_overdue * 20  # 20 KES per day
            
            fine = Fine(
                student_id=borrow_record.student_id,
                borrow_record_id=borrow_record.id,
                amount=fine_amount,
                original_amount=fine_amount,
                reason=f'Late return - {days_overdue} days overdue'
            )
            db.session.add(fine)
        
        try:
            db.session.commit()
            flash(f'Book "{borrow_record.book_ref.title}" returned successfully', 'success')
            
            if borrow_record.student_id and borrow_record.is_overdue:
                flash(f'Fine of {fine_amount} KES applied for late return', 'warning')
                
            return redirect(url_for('borrowing.list_borrows'))
        except Exception as e:
            db.session.rollback()
            flash('Error processing return', 'error')
    
    return render_template('borrowing/return_form.html', borrow_record=borrow_record)

@borrowing_bp.route('/fines')
@login_required
def list_fines():
    fines = Fine.query.filter_by(paid=False).order_by(Fine.created_at.desc()).all()
    return render_template('borrowing/fines.html', fines=fines)

@borrowing_bp.route('/fines/<int:fine_id>/pay', methods=['POST'])
@login_required
def pay_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    
    if not fine.paid:
        fine.paid = True
        fine.paid_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash(f'Fine of {fine.amount} KES marked as paid', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error processing fine payment', 'error')
    
    return redirect(url_for('borrowing.list_fines'))