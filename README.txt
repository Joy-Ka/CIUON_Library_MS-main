CONFUCIUS INSTITUTE LIBRARY MANAGEMENT SYSTEM
MySQL 8.0 Database Setup Instructions

=====================================================
STEP 1: CREATE DATABASE
=====================================================

CREATE DATABASE IF NOT EXISTS confucius_library CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE confucius_library;

=====================================================
STEP 2: CREATE TABLES
=====================================================

-- Users Table
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'librarian',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Category Table
CREATE TABLE category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Student Table
CREATE TABLE student (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    registration_number VARCHAR(50) UNIQUE,
    id_number VARCHAR(20) UNIQUE,
    passport_number VARCHAR(20) UNIQUE,
    email VARCHAR(120) NOT NULL,
    phone VARCHAR(20),
    membership_status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_reg_number (registration_number),
    INDEX idx_id_number (id_number),
    INDEX idx_passport (passport_number),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Staff Table
CREATE TABLE staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    staff_type VARCHAR(20) NOT NULL,
    email VARCHAR(120),
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_staff_type (staff_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Book Table
CREATE TABLE book (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(200),
    publisher VARCHAR(200),
    isbn VARCHAR(20) UNIQUE,
    unique_id VARCHAR(50) UNIQUE NOT NULL,
    category_id INT,
    total_copies INT DEFAULT 1,
    shelf_location VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL,
    INDEX idx_title (title),
    INDEX idx_isbn (isbn),
    INDEX idx_unique_id (unique_id),
    INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Borrow Record Table
CREATE TABLE borrow_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    student_id INT,
    staff_id INT,
    borrowed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    due_date DATETIME NOT NULL,
    returned_at DATETIME,
    notes TEXT,
    FOREIGN KEY (book_id) REFERENCES book(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE,
    INDEX idx_book (book_id),
    INDEX idx_student (student_id),
    INDEX idx_staff (staff_id),
    INDEX idx_returned (returned_at),
    INDEX idx_due_date (due_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fine Table
CREATE TABLE fine (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    borrow_record_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    original_amount DECIMAL(10, 2),
    reason VARCHAR(200) DEFAULT 'Late return',
    paid BOOLEAN DEFAULT FALSE,
    paid_at DATETIME,
    waived BOOLEAN DEFAULT FALSE,
    waived_at DATETIME,
    waived_by INT,
    waiver_reason TEXT,
    adjustment_amount DECIMAL(10, 2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    FOREIGN KEY (borrow_record_id) REFERENCES borrow_record(id) ON DELETE CASCADE,
    FOREIGN KEY (waived_by) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_student (student_id),
    INDEX idx_paid (paid),
    INDEX idx_waived (waived)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit Log Table
CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INT,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_action (action),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Backup Log Table
CREATE TABLE backup_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(200) NOT NULL,
    created_by INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_size INT,
    status VARCHAR(20) DEFAULT 'completed',
    description TEXT,
    FOREIGN KEY (created_by) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Notification Preference Table
CREATE TABLE notification_preference (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    email_due_reminder BOOLEAN DEFAULT TRUE,
    email_overdue_notice BOOLEAN DEFAULT TRUE,
    days_before_due INT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Email Log Table
CREATE TABLE email_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recipient_email VARCHAR(120) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    email_type VARCHAR(50) NOT NULL,
    student_id INT,
    borrow_record_id INT,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'sent',
    error_message TEXT,
    FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
    FOREIGN KEY (borrow_record_id) REFERENCES borrow_record(id) ON DELETE CASCADE,
    INDEX idx_student (student_id),
    INDEX idx_borrow_record (borrow_record_id),
    INDEX idx_sent_at (sent_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

=====================================================
STEP 3: CREATE DEFAULT ADMIN USER
=====================================================

-- NOTE: This creates a default admin user
-- Username: admin
-- Password: admin123 (CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN!)

INSERT INTO user (username, email, password_hash, role, active)
VALUES ('admin', 'admin@confucius.ac.ke', 'scrypt:32768:8:1$YourHashHere', 'admin', TRUE);

-- IMPORTANT: The password_hash above is a placeholder. 
-- You need to generate the actual hash using the Flask application's password hashing function.
-- Login to the application and change the password immediately!

=====================================================
STEP 4: INSERT SAMPLE CATEGORIES (OPTIONAL)
=====================================================

INSERT INTO category (name, description) VALUES
('Chinese Language', 'Books related to Chinese language learning and linguistics'),
('Chinese Culture', 'Books about Chinese culture, history, and traditions'),
('Literature', 'Chinese and translated literary works'),
('Business', 'Books on Chinese business and economy'),
('Education', 'Educational materials and textbooks'),
('Reference', 'Dictionaries, encyclopedias, and reference materials');

=====================================================
NOTES FOR MYSQL 8.0 SETUP
=====================================================

1. Make sure MySQL 8.0 is installed and running
2. Create a database user with appropriate privileges:

   CREATE USER 'library_user'@'localhost' IDENTIFIED BY 'your_strong_password';
   GRANT ALL PRIVILEGES ON confucius_library.* TO 'library_user'@'localhost';
   FLUSH PRIVILEGES;

3. Update your Flask application's DATABASE_URL environment variable:

   DATABASE_URL=mysql+pymysql://library_user:your_strong_password@localhost/confucius_library

4. Install MySQL Python connector:

   pip install pymysql

5. The application uses SQLAlchemy ORM which will handle most database operations.
   These SQL commands are for initial setup and understanding the schema.

=====================================================
IMPORTANT SECURITY NOTES
=====================================================

1. CHANGE the default admin password immediately after first login
2. Use strong passwords for database users
3. Restrict database access to localhost only in production
4. Regularly backup your database
5. Keep MySQL updated to the latest stable version
6. Use SSL/TLS for database connections in production

=====================================================
CONNECTION STRING FORMAT
=====================================================

For local development:
mysql+pymysql://username:password@localhost:3306/confucius_library

For production (with SSL):
mysql+pymysql://username:password@host:3306/confucius_library?ssl_ca=/path/to/ca.pem

=====================================================
BACKUP COMMAND
=====================================================

To backup the database:
mysqldump -u library_user -p confucius_library > backup_$(date +%Y%m%d_%H%M%S).sql

To restore from backup:
mysql -u library_user -p confucius_library < backup_file.sql

=====================================================

EMAIL NOTIFICATION SETUP
=====================================================

For detailed instructions on configuring Gmail SMTP for sending real email notifications,
please see the EMAIL_SETUP.md file in the project root directory.

Quick Setup:
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password from Google Account Security settings
3. Add GMAIL_USER and GMAIL_APP_PASSWORD to Replit Secrets
4. Restart the application
5. Test using the "Test Email" button on the Dashboard

=====================================================