"""Attribute models for fine-grained permissions."""
from app import db
from datetime import datetime


class Attribute(db.Model):
    """System attribute for granular permissions.
    
    Attributes are permission strings like 'lab.patient.read' that
    determine what actions a user can perform.
    """
    
    __tablename__ = 'attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, index=True)  # 'lab', 'system', etc.
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    role_attributes = db.relationship('RoleAttribute', backref='attribute', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Attribute {self.name}>'
    
    @classmethod
    def get_lab_attributes(cls):
        """Get all lab-related attributes."""
        return cls.query.filter_by(category='lab', is_active=True).all()
    
    @classmethod
    def get_system_attributes(cls):
        """Get all system-related attributes."""
        return cls.query.filter_by(category='system', is_active=True).all()


class RoleAttribute(db.Model):
    """Mapping between roles and attributes.
    
    This allows roles to have multiple attributes and attributes
    to be assigned to multiple roles.
    """
    
    __tablename__ = 'role_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False, index=True)  # 'admin', 'member', 'viewer'
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=True)  # Null for system-wide
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who granted this
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one attribute per role per lab
    __table_args__ = (
        db.UniqueConstraint('role_name', 'attribute_id', 'lab_id', name='unique_role_attribute_lab'),
    )
    
    # Relationships
    lab = db.relationship('Lab', backref='role_attributes')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self):
        lab_info = f' in Lab {self.lab_id}' if self.lab_id else ' (system-wide)'
        return f'<RoleAttribute {self.role_name} -> {self.attribute.name}{lab_info}>'


class UserLabAttribute(db.Model):
    """Direct user-specific attributes within a lab.
    
    This allows lab owners to grant specific attributes to users
    beyond their role-based attributes.
    """
    
    __tablename__ = 'user_lab_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Unique constraint: one attribute per user per lab
    __table_args__ = (
        db.UniqueConstraint('user_id', 'lab_id', 'attribute_id', name='unique_user_lab_attribute'),
    )
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='lab_attributes')
    lab = db.relationship('Lab', backref='user_attributes')
    granted_by_user = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self):
        return f'<UserLabAttribute User {self.user_id} -> {self.attribute.name} in Lab {self.lab_id}>'
    
    def is_expired(self):
        """Check if this attribute grant has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if this attribute grant is currently valid."""
        return self.is_active and not self.is_expired()