from werkzeug.security import generate_password_hash
from models import User, Category, Book, Student, Staff, db

def seed_initial_data():
    """Seed initial data for the Confucius Institute Library System"""
    
    # Create admin and librarian users
    admin_user = User(
        username='admin',
        email='admin@confucius.uonbi.ac.ke',
        password_hash=generate_password_hash('admin123'),
        role='admin'
    )
    
    librarian_user = User(
        username='librarian',
        email='librarian@confucius.uonbi.ac.ke',
        password_hash=generate_password_hash('librarian123'),
        role='librarian'
    )
    
    db.session.add(admin_user)
    db.session.add(librarian_user)
    
    # Create HSK categories
    hsk_categories = [
        Category(name='HSK 1', description='Beginner level Chinese language learning materials'),
        Category(name='HSK 2', description='Elementary level Chinese language learning materials'),
        Category(name='HSK 3', description='Intermediate level Chinese language learning materials'),
        Category(name='HSK 4', description='Upper intermediate level Chinese language learning materials'),
        Category(name='HSK 5', description='Advanced level Chinese language learning materials'),
        Category(name='Culture', description='Chinese culture and history materials'),
        Category(name='Literature', description='Chinese literature and poetry'),
        Category(name='Business Chinese', description='Business and professional Chinese materials')
    ]
    
    for category in hsk_categories:
        db.session.add(category)
    
    # Commit categories first to get their IDs
    db.session.commit()
    
    # Create sample books
    sample_books = [
        Book(title='HSK Standard Course 1', author='Jiang Liping', publisher='Beijing Language and Culture University Press', 
             unique_id='HSK1-001', category_id=1, total_copies=3, shelf_location='A1-01'),
        Book(title='HSK Standard Course 2', author='Jiang Liping', publisher='Beijing Language and Culture University Press', 
             unique_id='HSK2-001', category_id=2, total_copies=3, shelf_location='A1-02'),
        Book(title='HSK Standard Course 3', author='Jiang Liping', publisher='Beijing Language and Culture University Press', 
             unique_id='HSK3-001', category_id=3, total_copies=2, shelf_location='A1-03'),
        Book(title='New Practical Chinese Reader 1', author='Liu Xun', publisher='Beijing Language and Culture University Press', 
             unique_id='NPCR1-001', category_id=1, total_copies=4, shelf_location='A2-01'),
        Book(title='Chinese Cultural Reader', author='Wang Li', publisher='Foreign Language Teaching and Research Press', 
             unique_id='CCR-001', category_id=6, total_copies=2, shelf_location='B1-01'),
        Book(title='Business Chinese Conversation', author='Zhang Wei', publisher='Commercial Press', 
             unique_id='BCC-001', category_id=8, total_copies=2, shelf_location='C1-01')
    ]
    
    for book in sample_books:
        db.session.add(book)
    
    # Create sample students
    sample_students = [
        Student(name='John Kimani', registration_number='P15/1234/2023', email='j.kimani@students.uonbi.ac.ke', 
                phone='+254712345678', membership_status='active'),
        Student(name='Grace Wanjiku', registration_number='P15/5678/2023', email='g.wanjiku@students.uonbi.ac.ke', 
                phone='+254723456789', membership_status='active'),
        Student(name='David Ochieng', id_number='34567890', email='d.ochieng@gmail.com', 
                phone='+254734567890', membership_status='active'),
        Student(name='Liu Wei', passport_number='EF123456', email='liu.wei@example.com', 
                phone='+254745678901', membership_status='active')
    ]
    
    for student in sample_students:
        db.session.add(student)
    
    # Create sample staff
    sample_staff = [
        Staff(name='Dr. Li Ming', staff_type='teacher', email='li.ming@confucius.uonbi.ac.ke', 
              phone='+254756789012'),
        Staff(name='Sarah Muthoni', staff_type='teacher', email='s.muthoni@confucius.uonbi.ac.ke', 
              phone='+254767890123'),
        Staff(name='Wang Xiaoli', staff_type='intern', email='wang.xiaoli@confucius.uonbi.ac.ke', 
              phone='+254778901234')
    ]
    
    for staff in sample_staff:
        db.session.add(staff)
    
    try:
        db.session.commit()
        print("Initial data seeded successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding data: {e}")