from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import Staff, BorrowRecord, db
from sqlalchemy import or_
from utils.audit_logger import log_action

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/')
@login_required
def list_staff():
    search = request.args.get('search', '')
    if search:
        staff_members = Staff.query.filter(Staff.name.contains(search)).all()
    else:
        staff_members = Staff.query.all()
    
    return render_template('staff/list.html', staff_members=staff_members, search=search)

@staff_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_staff():
    if request.method == 'POST':
        staff = Staff(
            name=request.form['name'],
            staff_type=request.form['staff_type'],
            email=request.form.get('email', ''),
            phone=request.form.get('phone', '')
        )
        
        try:
            db.session.add(staff)
            db.session.commit()
            
            # Log the action
            log_action(
                action='CREATE_STAFF',
                entity_type='Staff',
                entity_id=staff.id,
                details={
                    'name': staff.name,
                    'staff_type': staff.staff_type,
                    'email': staff.email
                }
            )
            
            flash(f'Staff member {staff.name} added successfully', 'success')
            return redirect(url_for('staff.list_staff'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding staff member', 'error')
    
    return render_template('staff/form.html')

@staff_bp.route('/<int:staff_id>')
@login_required
def view_staff(staff_id):
    staff_member = Staff.query.get_or_404(staff_id)
    borrow_history = BorrowRecord.query.filter_by(staff_id=staff_id).order_by(BorrowRecord.borrowed_at.desc()).all()
    
    return render_template('staff/detail.html', 
                         staff_member=staff_member, 
                         borrow_history=borrow_history)

@staff_bp.route('/<int:staff_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_staff(staff_id):
    staff_member = Staff.query.get_or_404(staff_id)
    
    if request.method == 'POST':
        staff_member.name = request.form['name']
        staff_member.staff_type = request.form['staff_type']
        staff_member.email = request.form.get('email', '')
        staff_member.phone = request.form.get('phone', '')
        
        try:
            db.session.commit()
            
            # Log the action
            log_action(
                action='UPDATE_STAFF',
                entity_type='Staff',
                entity_id=staff_member.id,
                details={
                    'name': staff_member.name,
                    'staff_type': staff_member.staff_type,
                    'email': staff_member.email
                }
            )
            
            flash(f'Staff member {staff_member.name} updated successfully', 'success')
            return redirect(url_for('staff.view_staff', staff_id=staff_member.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating staff member', 'error')
    
    return render_template('staff/form.html', staff_member=staff_member)

@staff_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for staff search in borrowing forms"""
    query = request.args.get('q', '')
    if query:
        staff_members = Staff.query.filter(Staff.name.contains(query)).limit(10).all()
        
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'staff_type': s.staff_type
        } for s in staff_members])
    
    return jsonify([])