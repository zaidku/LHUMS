"""Lab model for multi-tenant support."""
from datetime import datetime
from app import db


class Lab(db.Model):
    """Lab model representing different tenant labs."""
    
    __tablename__ = 'labs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    memberships = db.relationship('LabMembership', back_populates='lab', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lab {self.code}>'


class LabMembership(db.Model):
    """Association table for User-Lab relationships with roles."""
    
    __tablename__ = 'lab_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='member')  # admin, member, viewer
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='lab_memberships')
    lab = db.relationship('Lab', back_populates='memberships')
    
    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        db.UniqueConstraint('user_id', 'lab_id', name='unique_user_lab'),
    )
    
    def __repr__(self):
        return f'<LabMembership user_id={self.user_id} lab_id={self.lab_id} role={self.role}>'
