"""Attribute-based authorization decorators."""
from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models import User
from app.routes.auth import get_user_attributes


def require_attributes(required_attributes, lab_id_param='lab_id', user_id_param=None):
    """Decorator to require specific attributes for accessing a route.
    
    Args:
        required_attributes (list): List of attribute names required
        lab_id_param (str): Name of parameter/field containing lab_id
        user_id_param (str): Name of parameter/field containing user_id (optional, defaults to current user)
    
    Usage:
        @require_attributes(['lab.patient.read', 'lab.reports.view'])
        @require_attributes(['lab.admin.manage'], lab_id_param='lab_id')
        @require_attributes(['lab.data.delete'], lab_id_param='lab_id', user_id_param='target_user_id')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # Get current user
                current_user_id = get_jwt_identity()
                current_user = User.query.get(current_user_id)
                
                if not current_user or not current_user.is_active:
                    return jsonify({'error': 'User not found or inactive'}), 401
                
                # Get lab_id from request
                lab_id = None
                
                # Try to get lab_id from URL parameters, JSON body, or form data
                if lab_id_param in kwargs:
                    lab_id = kwargs[lab_id_param]
                elif request.is_json and request.json and lab_id_param in request.json:
                    lab_id = request.json[lab_id_param]
                elif lab_id_param in request.args:
                    lab_id = request.args.get(lab_id_param)
                elif lab_id_param in request.form:
                    lab_id = request.form.get(lab_id_param)
                
                if not lab_id:
                    return jsonify({'error': f'Lab ID ({lab_id_param}) is required'}), 400
                
                # Determine which user to check (current user or specified user)
                target_user_id = current_user_id
                if user_id_param:
                    if user_id_param in kwargs:
                        target_user_id = kwargs[user_id_param]
                    elif request.is_json and request.json and user_id_param in request.json:
                        target_user_id = request.json[user_id_param]
                    elif user_id_param in request.args:
                        target_user_id = request.args.get(user_id_param)
                    elif user_id_param in request.form:
                        target_user_id = request.form.get(user_id_param)
                
                # Get user attributes
                user_attributes = get_user_attributes(target_user_id, lab_id)
                
                # Check if user has all required attributes
                missing_attributes = []
                for attr in required_attributes:
                    if attr not in user_attributes:
                        missing_attributes.append(attr)
                
                if missing_attributes:
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'required_attributes': required_attributes,
                        'missing_attributes': missing_attributes,
                        'user_attributes': user_attributes
                    }), 403
                
                # Store attributes in Flask's g object for use in the route
                g.user_attributes = user_attributes
                g.lab_id = lab_id
                g.target_user_id = target_user_id
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'error': f'Authorization check failed: {str(e)}'}), 500
                
        return decorated_function
    return decorator


def require_any_attributes(required_attributes, lab_id_param='lab_id', user_id_param=None):
    """Decorator to require at least one of the specified attributes.
    
    Args:
        required_attributes (list): List of attribute names (user needs at least one)
        lab_id_param (str): Name of parameter/field containing lab_id
        user_id_param (str): Name of parameter/field containing user_id (optional)
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            try:
                # Get current user
                current_user_id = get_jwt_identity()
                current_user = User.query.get(current_user_id)
                
                if not current_user or not current_user.is_active:
                    return jsonify({'error': 'User not found or inactive'}), 401
                
                # Get lab_id
                lab_id = None
                if lab_id_param in kwargs:
                    lab_id = kwargs[lab_id_param]
                elif request.is_json and request.json and lab_id_param in request.json:
                    lab_id = request.json[lab_id_param]
                elif lab_id_param in request.args:
                    lab_id = request.args.get(lab_id_param)
                elif lab_id_param in request.form:
                    lab_id = request.form.get(lab_id_param)
                
                if not lab_id:
                    return jsonify({'error': f'Lab ID ({lab_id_param}) is required'}), 400
                
                # Determine target user
                target_user_id = current_user_id
                if user_id_param:
                    if user_id_param in kwargs:
                        target_user_id = kwargs[user_id_param]
                    elif request.is_json and request.json and user_id_param in request.json:
                        target_user_id = request.json[user_id_param]
                    elif user_id_param in request.args:
                        target_user_id = request.args.get(user_id_param)
                
                # Get user attributes
                user_attributes = get_user_attributes(target_user_id, lab_id)
                
                # Check if user has at least one required attribute
                has_required_attribute = any(attr in user_attributes for attr in required_attributes)
                
                if not has_required_attribute:
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'required_attributes': required_attributes,
                        'message': 'User must have at least one of the required attributes',
                        'user_attributes': user_attributes
                    }), 403
                
                # Store attributes in Flask's g object
                g.user_attributes = user_attributes
                g.lab_id = lab_id
                g.target_user_id = target_user_id
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({'error': f'Authorization check failed: {str(e)}'}), 500
                
        return decorated_function
    return decorator


def require_lab_admin(lab_id_param='lab_id'):
    """Decorator to require lab admin role.
    
    This is a convenience decorator for lab administration routes.
    """
    return require_attributes(['lab.admin.manage'], lab_id_param=lab_id_param)


def require_lab_member(lab_id_param='lab_id'):
    """Decorator to require basic lab membership.
    
    This checks for basic lab access attributes.
    """
    return require_any_attributes([
        'lab.member.basic',
        'lab.admin.manage',
        'lab.viewer.read'
    ], lab_id_param=lab_id_param)


def check_user_attributes(user_id, lab_id, required_attributes):
    """Utility function to check if a user has required attributes.
    
    Returns:
        tuple: (has_access: bool, user_attributes: list, missing_attributes: list)
    """
    try:
        user_attributes = get_user_attributes(user_id, lab_id)
        missing_attributes = [attr for attr in required_attributes if attr not in user_attributes]
        has_access = len(missing_attributes) == 0
        
        return has_access, user_attributes, missing_attributes
        
    except Exception:
        return False, [], required_attributes


def get_current_user_attributes():
    """Get attributes for the current user from Flask's g object.
    
    This function should be called within a route protected by attribute decorators.
    """
    return getattr(g, 'user_attributes', [])


def get_current_lab_id():
    """Get lab_id for the current request from Flask's g object."""
    return getattr(g, 'lab_id', None)


def get_target_user_id():
    """Get target_user_id for the current request from Flask's g object."""
    return getattr(g, 'target_user_id', None)