from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Fine, Student, BorrowRecord, db
from utils.audit_logger import log_action
from datetime import datetime

fines_bp = Blueprint('fines', __name__)

@fines_bp.route('/')
@login_required
def list_fines():
    status = request.args.get('status', 'unpaid')
    
    query = Fine.query
    
    if status == 'unpaid':
        query = query.filter_by(paid=False, waived=False)
    elif status == 'paid':
        query = query.filter_by(paid=True)
    elif status == 'waived':
        query = query.filter_by(waived=True)
    
    fines = query.order_by(Fine.created_at.desc()).all()
    
    return render_template('fines/list.html', fines=fines, status=status)

@fines_bp.route('/<int:fine_id>/adjust', methods=['GET', 'POST'])
@login_required
def adjust_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    
    if request.method == 'POST':
        action_type = request.form['action_type']
        reason = request.form['reason']
        
        original_amount = fine.amount
        
        if action_type == 'waive':
            fine.waived = True
            fine.waived_at = datetime.utcnow()
            fine.waived_by = current_user.id
            fine.waiver_reason = reason
            fine.amount = 0.0
            fine.adjustment_amount = -original_amount
            
            log_action(
                action='WAIVE_FINE',
                entity_type='Fine',
                entity_id=fine.id,
                details={
                    'original_amount': original_amount,
                    'reason': reason,
                    'student_id': fine.student_id,
                    'borrow_record_id': fine.borrow_record_id
                }
            )
            
            flash(f'Fine of KES {original_amount} has been waived', 'success')
            
        elif action_type == 'adjust':
            new_amount = float(request.form['new_amount'])
            
            if new_amount < 0:
                flash('Fine amount cannot be negative', 'error')
                return render_template('fines/adjust.html', fine=fine)
            
            adjustment = new_amount - original_amount
            fine.amount = new_amount
            fine.adjustment_amount = adjustment
            fine.waiver_reason = reason
            fine.waived_by = current_user.id
            fine.waived_at = datetime.utcnow()
            
            log_action(
                action='ADJUST_FINE',
                entity_type='Fine',
                entity_id=fine.id,
                details={
                    'original_amount': original_amount,
                    'new_amount': new_amount,
                    'adjustment_amount': adjustment,
                    'reason': reason,
                    'student_id': fine.student_id,
                    'borrow_record_id': fine.borrow_record_id
                }
            )
            
            if adjustment > 0:
                flash(f'Fine increased by KES {adjustment} to KES {new_amount}', 'warning')
            elif adjustment < 0:
                flash(f'Fine reduced by KES {abs(adjustment)} to KES {new_amount}', 'success')
            else:
                flash('Fine amount unchanged', 'info')
        
        try:
            db.session.commit()
            return redirect(url_for('fines.list_fines'))
        except Exception as e:
            db.session.rollback()
            flash('Error adjusting fine', 'error')
    
    return render_template('fines/adjust.html', fine=fine)

@fines_bp.route('/<int:fine_id>/pay', methods=['POST'])
@login_required
def pay_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    
    if fine.paid:
        flash('Fine has already been paid', 'warning')
        return redirect(url_for('fines.list_fines'))
    
    if fine.waived:
        flash('Fine has been waived and cannot be paid', 'warning')
        return redirect(url_for('fines.list_fines'))
    
    fine.paid = True
    fine.paid_at = datetime.utcnow()
    
    log_action(
        action='PAY_FINE',
        entity_type='Fine',
        entity_id=fine.id,
        details={
            'amount': fine.amount,
            'student_id': fine.student_id,
            'borrow_record_id': fine.borrow_record_id
        }
    )
    
    try:
        db.session.commit()
        flash(f'Fine of KES {fine.amount} marked as paid', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error processing payment', 'error')
    
    return redirect(url_for('fines.list_fines'))

@fines_bp.route('/statistics')
@login_required
def fine_statistics():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Calculate statistics
    total_fines = Fine.query.count()
    paid_fines = Fine.query.filter_by(paid=True).count()
    waived_fines = Fine.query.filter_by(waived=True).count()
    unpaid_fines = Fine.query.filter_by(paid=False, waived=False).count()
    
    total_amount_collected = db.session.query(db.func.sum(Fine.amount)).filter_by(paid=True).scalar() or 0
    total_amount_waived = db.session.query(db.func.sum(Fine.original_amount)).filter_by(waived=True).scalar() or 0
    total_amount_pending = db.session.query(db.func.sum(Fine.amount)).filter_by(paid=False, waived=False).scalar() or 0
    
    # Get recent adjustments
    recent_adjustments = Fine.query.filter(
        Fine.waived_by.isnot(None)
    ).order_by(Fine.waived_at.desc()).limit(10).all()
    
    stats = {
        'total_fines': total_fines,
        'paid_fines': paid_fines,
        'waived_fines': waived_fines,
        'unpaid_fines': unpaid_fines,
        'total_amount_collected': total_amount_collected,
        'total_amount_waived': total_amount_waived,
        'total_amount_pending': total_amount_pending,
        'recent_adjustments': recent_adjustments
    }
    
    return render_template('fines/statistics.html', **stats)