# Confucius Institute Library Management System

## Overview

This is a web-based Library Management System built for the Confucius Institute at the University of Nairobi using Python Flask framework and SQLite database. The system manages books, students, staff, borrowing operations, and generates reports for library administration. It supports role-based access control with Admin and Librarian roles, handles different types of borrowers (UoN students, Kenyan non-UoN students, international students, and staff), and implements automated fine calculation for overdue books.

**Current Status:** Fully functional library management system with all core features implemented and operational. The Flask server is running on port 5000 with seeded initial data including sample users, books, categories, students, and staff.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask for server-side rendering
- **UI Framework**: Bootstrap 5.1.3 with Bootstrap Icons for responsive design
- **Layout Structure**: Base template with extension blocks for consistent styling
- **Custom Styling**: Chinese Institute branding with red color scheme (#d32f2f)

### Backend Architecture
- **Web Framework**: Flask with Blueprint-based modular architecture
- **Authentication**: Flask-Login for session management and role-based access control
- **Database ORM**: SQLAlchemy with Flask-SQLAlchemy extension
- **Migration System**: Flask-Migrate for database schema versioning
- **Security**: Werkzeug password hashing for user credentials

### Blueprint Organization
- **auth**: User authentication (login/logout)
- **dashboard**: Main dashboard with statistics and overview
- **students**: Student management and CRUD operations
- **staff**: Staff management for teachers and interns
- **books**: Book and category management with search functionality
- **borrowing**: Borrowing and return operations with due date tracking
- **reports**: Administrative reporting (admin role only)

### Data Storage Solutions
- **Primary Database**: SQLite for development/local deployment
- **Database Models**:
  - User: Admin/Librarian accounts with role-based permissions
  - Student: Supports UoN registration numbers, Kenyan ID numbers, or international passports
  - Staff: Teachers and interns (no fines applied)
  - Book: Title, author, ISBN, categories, stock tracking
  - Category: HSK levels (1-5), Culture, and custom categories
  - BorrowRecord: Tracking with automatic due date calculation (3 days for students)
  - Fine: Automated fine calculation (20 KES per day overdue) for students only

### Authentication and Authorization
- **Role-Based Access**: Admin (full control) and Librarian (daily operations)
- **Session Management**: Flask-Login with user_loader callback
- **Password Security**: Werkzeug password hashing
- **Access Control**: Route-level protection with @login_required decorators
- **Default Credentials**: Admin (admin/admin123), Librarian (librarian/librarian123)

### Business Logic Features
- **Student Borrowing Rules**: 3-book limit, 3-day loan period, automatic fine calculation
- **Staff Borrowing Rules**: Unlimited books, no fines, flexible return periods
- **Stock Management**: Available copies tracking with borrowing validation
- **Search Functionality**: Cross-model search for students, staff, and books
- **Report Generation**: Most borrowed books and active students (admin only)

## External Dependencies

### Python Packages
- **Flask**: Web framework and core application structure
- **Flask-SQLAlchemy**: Database ORM and model definitions
- **Flask-Migrate**: Database migration management
- **Flask-Login**: User session management and authentication
- **Werkzeug**: Password hashing and security utilities

### Frontend Dependencies
- **Bootstrap 5.1.3**: CSS framework via CDN for responsive UI components
- **Bootstrap Icons 1.7.2**: Icon library via CDN for consistent iconography

### Database
- **SQLite**: File-based database (confucius_library.db) for local development
- **Migration Support**: Ready for PostgreSQL or MySQL migration in production

### Configuration
- **Environment Variables**: SESSION_SECRET for session key configuration
- **Database URI**: Configurable for different database backends
- **Debug Mode**: Development configuration with SQLAlchemy query logging disabled