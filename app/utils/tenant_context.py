"""Tenant context for multi-lab data isolation."""
from flask import g
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.models.lab import LabMembership, Lab


def get_current_user_labs():
    """Get all lab IDs the current user has access to.
    
    Returns:
        list: List of lab IDs the user can access
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # System admins can access all labs
    if user and user.is_admin:
        return [lab.id for lab in Lab.query.filter_by(is_active=True).all()]
    
    # Regular users can only access their labs
    memberships = LabMembership.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()
    
    return [m.lab_id for m in memberships]


def get_current_lab():
    """Get the current lab from request context.
    
    Returns:
        int: Current lab ID from request context
    """
    return g.get('current_lab_id')


def set_current_lab(lab_id):
    """Set the current lab in request context.
    
    Args:
        lab_id: Lab ID to set as current
    """
    g.current_lab_id = lab_id


def verify_lab_access(lab_id):
    """Verify current user has access to the specified lab.
    
    Args:
        lab_id: Lab ID to verify access to
        
    Returns:
        bool: True if user has access, False otherwise
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # System admins can access all labs
    if user and user.is_admin:
        return True
    
    # Check if user has active membership in this lab
    membership = LabMembership.query.filter_by(
        user_id=user_id,
        lab_id=lab_id,
        is_active=True
    ).first()
    
    return membership is not None


def get_user_role_in_lab(lab_id):
    """Get the current user's role in a specific lab.
    
    Args:
        lab_id: Lab ID to check role for
        
    Returns:
        str: User's role in the lab (admin, member, viewer) or None if not a member
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # System admins have admin role in all labs
    if user and user.is_admin:
        return 'admin'
    
    membership = LabMembership.query.filter_by(
        user_id=user_id,
        lab_id=lab_id,
        is_active=True
    ).first()
    
    return membership.role if membership else None


def is_lab_admin(lab_id):
    """Check if current user is an admin in the specified lab.
    
    Args:
        lab_id: Lab ID to check admin status for
        
    Returns:
        bool: True if user is lab admin or system admin, False otherwise
    """
    role = get_user_role_in_lab(lab_id)
    return role == 'admin'
