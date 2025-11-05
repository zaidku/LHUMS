"""Token models for password reset and email verification."""
from datetime import datetime, timedelta
from app import db
import secrets


class PasswordResetToken(db.Model):
    """Password reset token model."""
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('reset_tokens', lazy='dynamic'))
    
    def __init__(self, user_id, expires_in_hours=24):
        """Initialize password reset token.
        
        Args:
            user_id: ID of the user
            expires_in_hours: Token validity period (default 24 hours)
        """
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    def is_valid(self):
        """Check if token is still valid."""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def mark_used(self):
        """Mark token as used."""
        self.used = True
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}... user_id={self.user_id}>'


class EmailVerificationToken(db.Model):
    """Email verification token model."""
    
    __tablename__ = 'email_verification_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)  # New email to verify
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('verification_tokens', lazy='dynamic'))
    
    def __init__(self, user_id, email, expires_in_hours=48):
        """Initialize email verification token.
        
        Args:
            user_id: ID of the user
            email: Email address to verify
            expires_in_hours: Token validity period (default 48 hours)
        """
        self.user_id = user_id
        self.email = email
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    def is_valid(self):
        """Check if token is still valid."""
        return not self.used and datetime.utcnow() < self.expires_at
    
    def mark_used(self):
        """Mark token as used."""
        self.used = True
    
    def __repr__(self):
        return f'<EmailVerificationToken {self.token[:8]}... email={self.email}>'


class AuditLog(db.Model):
    """Audit log for tracking user actions and security events."""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(50))  # user, lab, membership, etc.
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string with additional details
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(255))
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))
    
    # Action types constants
    ACTION_LOGIN = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_REGISTER = 'register'
    ACTION_PASSWORD_RESET_REQUEST = 'password_reset_request'
    ACTION_PASSWORD_RESET = 'password_reset'
    ACTION_PASSWORD_CHANGE = 'password_change'
    ACTION_EMAIL_CHANGE = 'email_change'
    ACTION_PROFILE_UPDATE = 'profile_update'
    ACTION_USER_DELETE = 'user_delete'
    ACTION_LAB_CREATE = 'lab_create'
    ACTION_LAB_UPDATE = 'lab_update'
    ACTION_LAB_DELETE = 'lab_delete'
    ACTION_MEMBER_ADD = 'member_add'
    ACTION_MEMBER_REMOVE = 'member_remove'
    ACTION_ROLE_UPDATE = 'role_update'
    ACTION_FAILED_LOGIN = 'failed_login'
    
    def __repr__(self):
        return f'<AuditLog {self.action} user_id={self.user_id} at {self.created_at}>'


class LoginAttempt(db.Model):
    """Track login attempts for security."""
    
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<LoginAttempt {self.username} success={self.success} at {self.created_at}>'
