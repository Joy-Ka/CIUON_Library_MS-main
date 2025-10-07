# Confucius Institute Library Management System

## Overview

This is a web-based Library Management System built for the Confucius Institute at the University of Nairobi using Python Flask framework. The system manages books, students, staff, borrowing operations, and generates reports for library administration. It supports role-based access control with Admin and Librarian roles, handles different types of borrowers (UoN students, Kenyan non-UoN students, international students, and staff), and implements automated fine calculation for overdue books.

**Current Status:** Fully functional library management system with all core features implemented and operational. The Flask server is running on port 5000 with PostgreSQL database (production) with fallback to SQLite for local development. All templates have been created with Tailwind CSS styling and Confucius Institute red theme branding.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask for server-side rendering
- **UI Framework**: Tailwind CSS 3.x (CDN) for modern utility-first styling with Bootstrap 5.1.3 for legacy components
- **Icons**: Bootstrap Icons 1.7.2 for consistent iconography
- **Layout Structure**: Vertical sidebar navigation with responsive mobile toggle
- **Navigation**: Left sidebar layout with collapsible mobile menu
- **Custom Styling**: Confucius Institute branding with red color scheme (#d32f2f)
- **Responsive Design**: Mobile-first approach with hamburger menu for small screens

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
- **Database Configuration**: Flexible database setup supporting both PostgreSQL (production via DATABASE_URL) and SQLite (local development fallback)
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
- **Tailwind CSS 3.x**: Primary utility-first CSS framework via CDN
- **Bootstrap 5.1.3**: CSS framework via CDN for form components and alerts
- **Bootstrap Icons 1.7.2**: Icon library via CDN for consistent iconography

### Database
- **PostgreSQL**: Production database via Replit's managed PostgreSQL (DATABASE_URL environment variable)
- **SQLite**: Fallback database for local development when DATABASE_URL is not set
- **Migration Support**: Flask-Migrate for schema management and versioning
- **Security**: Password hash fields sized for scrypt algorithm (256 characters)

### Configuration & Security
- **Environment Variables**: 
  - SESSION_SECRET (required): Flask session secret key - application will not start without this
  - DATABASE_URL (optional): PostgreSQL connection string - falls back to SQLite if not provided
- **Database URI**: Automatically selects PostgreSQL or SQLite based on environment
- **Debug Mode**: Development configuration with SQLAlchemy query logging disabled
- **Security Requirements**: SESSION_SECRET must be set in environment to prevent security vulnerabilities

## Recent Changes (October 2025)

### Database Migration
- Migrated from SQLite-only to flexible PostgreSQL/SQLite configuration
- Added environment-aware database selection in app.py
- Fixed password_hash field length to support scrypt hashing (256 characters)
- Implemented proper PostgreSQL connection pooling with pool_recycle and pool_pre_ping

### Template Implementation
- Created 19+ missing templates with Tailwind CSS styling:
  - **Staff Module**: detail.html with borrowing history
  - **Books Module**: detail.html, categories.html, category_form.html
  - **Reports Module**: index.html, most_borrowed.html, active_students.html, category_trends.html, stock_status.html, overdue_items.html, staff_borrows.html, stock_depletion.html, inactive_students.html
  - **Audit Module**: list.html, entity_history.html, statistics.html
  - **Backup Module**: list.html
  - **Fines Module**: statistics.html, borrowing/fines.html
- All templates follow Confucius Institute red theme (#d32f2f)
- Responsive design with mobile-first approach
- Consistent use of Tailwind CSS utility classes with Bootstrap components

### Security Enhancements
- Removed hard-coded SECRET_KEY fallback to prevent security vulnerabilities
- Added runtime validation requiring SESSION_SECRET environment variable
- Application now raises RuntimeError if SESSION_SECRET is not set