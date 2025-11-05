"""Manual database initialization script for Python 3.13 compatibility."""
from app import create_app, db
from app.models import User, Lab, LabMembership, PasswordResetToken, EmailVerificationToken, AuditLog, LoginAttempt

def init_database():
    """Initialize the database by creating all tables."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Show created tables
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

def create_admin_user():
    """Create an admin user interactively."""
    app = create_app()
    
    with app.app_context():
        print("\n--- Create Admin User ---")
        username = input("Enter admin username: ")
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        first_name = input("Enter first name (optional): ")
        last_name = input("Enter last name (optional): ")
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"✗ Error: Username '{username}' already exists!")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"✗ Error: Email '{email}' already exists!")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None,
            is_admin=True,
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"\n✓ Admin user '{username}' created successfully!")
        print(f"  ID: {admin.id}")
        print(f"  Email: {admin.email}")
        print(f"  Is Admin: {admin.is_admin}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'create-admin':
        create_admin_user()
    else:
        init_database()
        print("\nTo create an admin user, run:")
        print("  python init_db.py create-admin")
