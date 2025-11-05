"""Application entry point."""
import os
from app import create_app, db
from app.models import User, Lab, LabMembership, PasswordResetToken, EmailVerificationToken, AuditLog, LoginAttempt

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        'db': db,
        'User': User,
        'Lab': Lab,
        'LabMembership': LabMembership,
        'PasswordResetToken': PasswordResetToken,
        'EmailVerificationToken': EmailVerificationToken,
        'AuditLog': AuditLog,
        'LoginAttempt': LoginAttempt
    }


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized successfully!')


@app.cli.command()
def create_admin():
    """Create an admin user."""
    username = input('Enter admin username: ')
    email = input('Enter admin email: ')
    password = input('Enter admin password: ')
    
    admin = User(
        username=username,
        email=email,
        is_admin=True
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    print(f'Admin user "{username}" created successfully!')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
