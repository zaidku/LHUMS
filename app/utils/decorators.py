"""Custom decorators for access control."""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.models.lab import LabMembership


def admin_required(fn):
    """Decorator to require admin privileges."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


def lab_admin_required(fn):
    """Decorator to require lab admin or system admin privileges."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # System admin can access all labs
        if user and user.is_admin:
            return fn(*args, **kwargs)
        
        # Check if user is lab admin
        lab_id = kwargs.get('lab_id')
        if lab_id:
            membership = LabMembership.query.filter_by(
                user_id=current_user_id,
                lab_id=lab_id,
                role='admin'
            ).first()
            
            if membership:
                return fn(*args, **kwargs)
        
        return jsonify({'error': 'Lab admin privileges required'}), 403
    
    return wrapper


def require_lab_access(fn):
    """Decorator to verify user has access to requested lab.
    
    This decorator ensures data isolation by:
    1. Extracting lab_id from URL, query params, or request body
    2. Verifying user has membership in the lab
    3. Setting lab context for use in the view function
    
    Usage:
        @require_lab_access
        def my_view(lab_id, ...):
            # lab_id is already validated
            # Current lab is set in context
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Extract lab_id from various sources
        lab_id = (
            kwargs.get('lab_id') or 
            request.args.get('lab_id', type=int) or 
            (request.get_json() or {}).get('lab_id')
        )
        
        if not lab_id:
            return jsonify({'error': 'Lab ID required'}), 400
        
        # Verify user has access to this lab
        from app.utils.tenant_context import verify_lab_access, set_current_lab
        
        if not verify_lab_access(lab_id):
            return jsonify({'error': 'Access to this lab is forbidden'}), 403
        
        # Store lab_id in context for use in views
        set_current_lab(lab_id)
        
        return fn(*args, **kwargs)
    
    return wrapper


def require_lab_role(required_role):
    """Decorator to require specific role in a lab.
    
    Args:
        required_role: Required role ('admin', 'member', or 'viewer')
        
    Usage:
        @require_lab_role('admin')
        def admin_only_view(lab_id, ...):
            # Only lab admins can access
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            lab_id = kwargs.get('lab_id')
            
            if not lab_id:
                return jsonify({'error': 'Lab ID required'}), 400
            
            from app.utils.tenant_context import get_user_role_in_lab
            
            role = get_user_role_in_lab(lab_id)
            
            if not role:
                return jsonify({'error': 'You are not a member of this lab'}), 403
            
            # Define role hierarchy: admin > member > viewer
            role_hierarchy = {'admin': 3, 'member': 2, 'viewer': 1}
            
            if role_hierarchy.get(role, 0) < role_hierarchy.get(required_role, 0):
                return jsonify({'error': f'{required_role.capitalize()} role required'}), 403
            
            return fn(*args, **kwargs)
        
        return wrapper
    return decorator
