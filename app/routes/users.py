"""User management routes."""
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app import db
from app.models.user import User
from app.schemas import user_schema, users_schema, user_update_schema
from app.utils.decorators import admin_required

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    """List all users (admin only)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Query users with pagination
        pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': users_schema.dump(pagination.items),
            'total': pagination.total,
            'page': pagination.page,
            'pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user by ID."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Users can view their own profile or admins can view any profile
        if current_user_id != user_id and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user_schema.dump(user)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_user(user_id):
    """Update user profile."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Users can update their own profile or admins can update any profile
        if current_user_id != user_id and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Store user_id in g for validation
        g.user_id = user_id
        
        # Validate and update data
        data = user_update_schema.load(request.get_json(), partial=True)
        
        for key, value in data.items():
            setattr(user, key, value)
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user_schema.dump(user)
        }), 200
        
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete user (admin only)."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>/labs', methods=['GET'])
@jwt_required()
def get_user_labs(user_id):
    """Get all labs a user is a member of."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Users can view their own labs or admins can view any user's labs
        if current_user_id != user_id and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        from app.schemas import lab_memberships_schema
        
        return jsonify({
            'memberships': lab_memberships_schema.dump(user.lab_memberships)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>/force-password-change', methods=['POST'])
@jwt_required()
@admin_required
def force_password_change(user_id):
    """Force user to change password on next login (admin only)."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.require_password_change = True
        db.session.commit()
        
        # Log the action
        from app.utils.audit import AuditLogger
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        AuditLogger.log(current_user_id, 'force_password_change',
                       resource_type='user', resource_id=user_id)
        
        # Send notification email
        from app.utils.email_service import EmailService
        try:
            EmailService.send_email(
                user.email,
                'Password Change Required',
                f'''<html><body>
                <h2>Password Change Required</h2>
                <p>Hi {user.first_name or user.username},</p>
                <p>An administrator has required you to change your password.</p>
                <p>You will be prompted to change your password on your next login.</p>
                <p>Best regards,<br>UMS Team</p>
                </body></html>'''
            )
        except:
            pass
        
        return jsonify({
            'message': 'User will be required to change password on next login'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>/unlock', methods=['POST'])
@jwt_required()
@admin_required
def unlock_user_account(user_id):
    """Unlock a locked user account (admin only)."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_locked():
            return jsonify({'message': 'Account is not locked'}), 200
        
        user.unlock_account()
        db.session.commit()
        
        # Log the action
        from app.utils.audit import AuditLogger
        from flask_jwt_extended import get_jwt_identity
        current_user_id = get_jwt_identity()
        AuditLogger.log(current_user_id, 'unlock_account',
                       resource_type='user', resource_id=user_id)
        
        return jsonify({
            'message': 'Account unlocked successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

