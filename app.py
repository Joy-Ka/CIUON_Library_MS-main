from flask import Flask, render_template, redirect, url_for
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
import os

# Import db from models
from models import db

# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-confucius-institute')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Import models (must be after db initialization)
    from models import User, Student, Staff, Book, Category, BorrowRecord, Fine, AuditLog, BackupLog, NotificationPreference, EmailLog
    
    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.students import students_bp
    from blueprints.staff import staff_bp
    from blueprints.books import books_bp
    from blueprints.borrowing import borrowing_bp
    from blueprints.reports import reports_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.fines import fines_bp
    from blueprints.audit import audit_bp
    from blueprints.backup import backup_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(students_bp, url_prefix='/students')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(borrowing_bp, url_prefix='/borrowing')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(fines_bp, url_prefix='/fines')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(backup_bp, url_prefix='/backup')
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Home route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    # Create database tables and seed data
    with app.app_context():
        db.create_all()
        
        # Check if we need to seed initial data
        if not User.query.first():
            from utils.seed_data import seed_initial_data
            seed_initial_data()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)