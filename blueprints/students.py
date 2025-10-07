from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import Student, BorrowRecord, Fine, db
from sqlalchemy import or_
from utils.audit_logger import log_action

students_bp = Blueprint('students', __name__)

@students_bp.route('/')
@login_required
def list_students():
    search = request.args.get('search', '')
    if search:
        students = Student.query.filter(
            or_(
                Student.name.contains(search),
                Student.registration_number.contains(search),
                Student.id_number.contains(search),
                Student.passport_number.contains(search)
            )
        ).all()
    else:
        students = Student.query.all()
    
    return render_template('students/list.html', students=students, search=search)

@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        # Validate that at least one identifier is provided
        reg_num = request.form.get('registration_number', '').strip()
        id_num = request.form.get('id_number', '').strip()
        passport_num = request.form.get('passport_number', '').strip()
        
        if not any([reg_num, id_num, passport_num]):
            flash('At least one identifier (Registration Number, ID Number, or Passport Number) is required', 'error')
            return render_template('students/form.html')
        
        student = Student(
            name=request.form['name'],
            registration_number=reg_num if reg_num else None,
            id_number=id_num if id_num else None,
            passport_number=passport_num if passport_num else None,
            email=request.form['email'],
            phone=request.form.get('phone', ''),
            membership_status=request.form.get('membership_status', 'active')
        )
        
        try:
            db.session.add(student)
            db.session.commit()
            
            # Log the action
            log_action(
                action='CREATE_STUDENT',
                entity_type='Student',
                entity_id=student.id,
                details={
                    'name': student.name,
                    'identifier': student.identifier,
                    'email': student.email,
                    'membership_status': student.membership_status
                }
            )
            
            flash(f'Student {student.name} added successfully', 'success')
            return redirect(url_for('students.list_students'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding student. Please check for duplicate identifiers.', 'error')
    
    return render_template('students/form.html')

@students_bp.route('/<int:student_id>')
@login_required
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    borrow_history = BorrowRecord.query.filter_by(student_id=student_id).order_by(BorrowRecord.borrowed_at.desc()).all()
    unpaid_fines = Fine.query.filter_by(student_id=student_id, paid=False).all()
    
    return render_template('students/detail.html', 
                         student=student, 
                         borrow_history=borrow_history,
                         unpaid_fines=unpaid_fines)

@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        reg_num = request.form.get('registration_number', '').strip()
        id_num = request.form.get('id_number', '').strip()
        passport_num = request.form.get('passport_number', '').strip()
        
        if not any([reg_num, id_num, passport_num]):
            flash('At least one identifier is required', 'error')
            return render_template('students/form.html', student=student)
        
        student.name = request.form['name']
        student.registration_number = reg_num if reg_num else None
        student.id_number = id_num if id_num else None
        student.passport_number = passport_num if passport_num else None
        student.email = request.form['email']
        student.phone = request.form.get('phone', '')
        student.membership_status = request.form.get('membership_status', 'active')
        
        try:
            db.session.commit()
            
            # Log the action
            log_action(
                action='UPDATE_STUDENT',
                entity_type='Student',
                entity_id=student.id,
                details={
                    'name': student.name,
                    'identifier': student.identifier,
                    'email': student.email,
                    'membership_status': student.membership_status
                }
            )
            
            flash(f'Student {student.name} updated successfully', 'success')
            return redirect(url_for('students.view_student', student_id=student.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating student', 'error')
    
    return render_template('students/form.html', student=student)

@students_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for student search in borrowing forms"""
    query = request.args.get('q', '')
    if query:
        students = Student.query.filter(
            or_(
                Student.name.contains(query),
                Student.registration_number.contains(query),
                Student.id_number.contains(query),
                Student.passport_number.contains(query)
            )
        ).limit(10).all()
        
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'identifier': s.identifier,
            'current_borrowed': s.current_borrowed_count
        } for s in students])
    
    return jsonify([])