"""User model."""
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """User model for authentication and profile management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    locked_until = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_login_at = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime)
    password_expires_at = db.Column(db.DateTime)  # For password rotation policy
    password_history = db.Column(db.Text)  # JSON array of previous password hashes
    require_password_change = db.Column(db.Boolean, default=False)  # Force password change
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lab_memberships = db.relationship('LabMembership', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password."""
        from datetime import timedelta
        import json
        
        # Store old password in history (for password reuse prevention)
        if self.password_hash:
            history = json.loads(self.password_history) if self.password_history else []
            history.append(self.password_hash)
            # Keep last 5 passwords in history (HIPAA recommendation)
            self.password_history = json.dumps(history[-5:])
        
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        
        # Set password expiration (90 days for HIPAA compliance)
        self.password_expires_at = datetime.utcnow() + timedelta(days=90)
        self.require_password_change = False
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_password_expired(self):
        """Check if password has expired (90-day rotation)."""
        if not self.password_expires_at:
            return False
        return datetime.utcnow() > self.password_expires_at
    
    def check_password_reuse(self, password):
        """Check if password was used before (prevents reuse)."""
        import json
        if not self.password_history:
            return False
        
        history = json.loads(self.password_history)
        for old_hash in history:
            if check_password_hash(old_hash, password):
                return True
        return False
    
    def is_locked(self):
        """Check if account is currently locked."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False
    
    def lock_account(self, duration_minutes=30):
        """Lock account for specified duration."""
        from datetime import timedelta
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.failed_login_attempts = 0
    
    def unlock_account(self):
        """Unlock account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def record_login_attempt(self, success=True):
        """Record login attempt."""
        if success:
            self.failed_login_attempts = 0
            self.last_login_at = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.lock_account()
    
    def __repr__(self):
        return f'<User {self.username}>'
