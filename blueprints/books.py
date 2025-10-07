from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import Book, Category, BorrowRecord, db
from sqlalchemy import or_
from utils.audit_logger import log_action

books_bp = Blueprint('books', __name__)

@books_bp.route('/')
@login_required
def list_books():
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', '')
    
    query = Book.query
    
    if search:
        query = query.filter(
            or_(
                Book.title.contains(search),
                Book.author.contains(search),
                Book.isbn.contains(search),
                Book.unique_id.contains(search)
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    books = query.all()
    categories = Category.query.all()
    
    return render_template('books/list.html', 
                         books=books, 
                         categories=categories, 
                         search=search, 
                         selected_category=category_id)

@books_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        if category_id == '':
            category_id = None
        
        book = Book(
            title=request.form['title'],
            author=request.form.get('author', ''),
            publisher=request.form.get('publisher', ''),
            isbn=request.form.get('isbn', ''),
            unique_id=request.form['unique_id'],
            category_id=category_id,
            total_copies=int(request.form.get('total_copies', 1)),
            shelf_location=request.form.get('shelf_location', '')
        )
        
        try:
            db.session.add(book)
            db.session.commit()
            
            # Log the action
            log_action(
                action='CREATE_BOOK',
                entity_type='Book',
                entity_id=book.id,
                details={
                    'title': book.title,
                    'author': book.author,
                    'unique_id': book.unique_id,
                    'isbn': book.isbn,
                    'total_copies': book.total_copies
                }
            )
            
            flash(f'Book "{book.title}" added successfully', 'success')
            return redirect(url_for('books.list_books'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding book. Please check for duplicate ISBN or Unique ID.', 'error')
    
    categories = Category.query.all()
    return render_template('books/form.html', categories=categories)

@books_bp.route('/<int:book_id>')
@login_required
def view_book(book_id):
    book = Book.query.get_or_404(book_id)
    borrow_history = BorrowRecord.query.filter_by(book_id=book_id).order_by(BorrowRecord.borrowed_at.desc()).all()
    current_borrows = BorrowRecord.query.filter_by(book_id=book_id, returned_at=None).all()
    
    return render_template('books/detail.html', 
                         book=book, 
                         borrow_history=borrow_history,
                         current_borrows=current_borrows)

@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        if category_id == '':
            category_id = None
            
        book.title = request.form['title']
        book.author = request.form.get('author', '')
        book.publisher = request.form.get('publisher', '')
        book.isbn = request.form.get('isbn', '')
        book.unique_id = request.form['unique_id']
        book.category_id = category_id
        book.total_copies = int(request.form.get('total_copies', 1))
        book.shelf_location = request.form.get('shelf_location', '')
        
        try:
            db.session.commit()
            
            # Log the action
            log_action(
                action='UPDATE_BOOK',
                entity_type='Book',
                entity_id=book.id,
                details={
                    'title': book.title,
                    'author': book.author,
                    'unique_id': book.unique_id,
                    'isbn': book.isbn,
                    'total_copies': book.total_copies
                }
            )
            
            flash(f'Book "{book.title}" updated successfully', 'success')
            return redirect(url_for('books.view_book', book_id=book.id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating book', 'error')
    
    categories = Category.query.all()
    return render_template('books/form.html', book=book, categories=categories)

@books_bp.route('/categories')
@login_required
def list_categories():
    categories = Category.query.all()
    return render_template('books/categories.html', categories=categories)

@books_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        category = Category(
            name=request.form['name'],
            description=request.form.get('description', '')
        )
        
        try:
            db.session.add(category)
            db.session.commit()
            
            # Log the action
            log_action(
                action='CREATE_CATEGORY',
                entity_type='Category',
                entity_id=category.id,
                details={
                    'name': category.name,
                    'description': category.description
                }
            )
            
            flash(f'Category "{category.name}" added successfully', 'success')
            return redirect(url_for('books.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding category. Category name must be unique.', 'error')
    
    return render_template('books/category_form.html')

@books_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for book search in borrowing forms"""
    query = request.args.get('q', '')
    if query:
        books = Book.query.filter(
            or_(
                Book.title.contains(query),
                Book.author.contains(query),
                Book.unique_id.contains(query)
            )
        ).filter(Book.available_copies > 0).limit(10).all()
        
        return jsonify([{
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'unique_id': b.unique_id,
            'available_copies': b.available_copies
        } for b in books])
    
    return jsonify([])