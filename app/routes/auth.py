"""Authentication routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime
from app import db
from app.models.user import User
from app.models.token import PasswordResetToken, EmailVerificationToken, LoginAttempt
from app.schemas import user_registration_schema, user_login_schema, user_schema
from app.utils.email_service import EmailService
from app.utils.audit import AuditLogger

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        # Validate request data
        data = user_registration_schema.load(request.get_json())
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        user.set_password(data['password'])
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        # Log registration
        AuditLogger.log_registration(user.id)
        
        # Send welcome email (async in production)
        try:
            EmailService.send_welcome_email(user)
        except:
            pass  # Don't fail registration if email fails
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user_schema.dump(user)
        }), 201
        
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens."""
    try:
        # Validate request data
        data = user_login_schema.load(request.get_json())
        
        # Find user
        user = User.query.filter_by(username=data['username']).first()
        
        # Verify credentials
        if not user:
            AuditLogger.log(None, 'failed_login', details={'username': data['username']}, success=False)
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Check if account is locked
        if user.is_locked():
            return jsonify({'error': 'Account is locked. Please try again later or reset your password.'}), 403
        
        if not user.check_password(data['password']):
            user.record_login_attempt(success=False)
            db.session.commit()
            
            AuditLogger.log(user.id, 'failed_login', success=False)
            
            # Send email if account gets locked
            if user.is_locked():
                try:
                    EmailService.send_account_locked_email(user)
                except:
                    pass
            
            return jsonify({'error': 'Invalid username or password'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403
        
        # Check if password is expired (HIPAA 90-day rotation)
        if user.is_password_expired():
            return jsonify({
                'error': 'Password expired',
                'message': 'Your password has expired. Please reset your password.',
                'password_expired': True
            }), 403
        
        # Check if forced password change is required
        if user.require_password_change:
            return jsonify({
                'error': 'Password change required',
                'message': 'Administrator has required you to change your password.',
                'require_password_change': True
            }), 403
        
        # Record successful login
        user.record_login_attempt(success=True)
        db.session.commit()
        
        # Log successful login
        AuditLogger.log_login(user.id, success=True)
        
        # Create JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_schema.dump(user)
        }), 200
        
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token."""
    try:
        current_user_id = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user profile."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user_schema.dump(user)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset email."""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        # Always return success to prevent email enumeration
        if not user:
            return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
        
        # Create password reset token
        token = PasswordResetToken(user.id)
        db.session.add(token)
        db.session.commit()
        
        # Log the request
        AuditLogger.log_password_reset_request(user.id, email)
        
        # Send reset email
        try:
            EmailService.send_password_reset_email(user, token.token)
        except Exception as e:
            return jsonify({'error': 'Failed to send reset email'}), 500
        
        return jsonify({
            'message': 'If the email exists, a reset link has been sent'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using token."""
    try:
        data = request.get_json()
        token_string = data.get('token')
        new_password = data.get('new_password')
        
        if not token_string or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Find and validate token
        token = PasswordResetToken.query.filter_by(token=token_string).first()
        
        if not token or not token.is_valid():
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        # Reset password
        user = User.query.get(token.user_id)
        user.set_password(new_password)
        user.password_changed_at = datetime.utcnow()
        user.unlock_account()  # Unlock if it was locked
        
        # Mark token as used
        token.mark_used()
        
        db.session.commit()
        
        # Log the reset
        AuditLogger.log_password_reset(user.id)
        
        # Send confirmation email
        try:
            EmailService.send_password_changed_email(user)
        except:
            pass
        
        return jsonify({
            'message': 'Password reset successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change password for authenticated user."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Check if new password was used before (HIPAA - prevent password reuse)
        if user.check_password_reuse(new_password):
            return jsonify({
                'error': 'Password was used previously',
                'message': 'Please choose a password you have not used before (last 5 passwords are blocked)'
            }), 400
        
        # Check if new password is same as current (redundant but explicit)
        if user.check_password(new_password):
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Log the change
        AuditLogger.log_password_change(user.id)
        
        # Send notification email
        try:
            EmailService.send_password_changed_email(user)
        except:
            pass
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-email', methods=['POST'])
@jwt_required()
def change_email():
    """Request email change with verification."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        new_email = data.get('new_email')
        password = data.get('password')
        
        if not new_email or not password:
            return jsonify({'error': 'New email and password are required'}), 400
        
        # Verify password
        if not user.check_password(password):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Check if email already exists
        if User.query.filter_by(email=new_email).first():
            return jsonify({'error': 'Email already in use'}), 400
        
        # Create verification token
        token = EmailVerificationToken(user.id, new_email)
        db.session.add(token)
        db.session.commit()
        
        # Send verification email
        try:
            EmailService.send_email_verification(user, token.token, new_email)
        except Exception as e:
            return jsonify({'error': 'Failed to send verification email'}), 500
        
        return jsonify({
            'message': 'Verification email sent to new address'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Verify email address using token."""
    try:
        data = request.get_json()
        token_string = data.get('token')
        
        if not token_string:
            return jsonify({'error': 'Token is required'}), 400
        
        # Find and validate token
        token = EmailVerificationToken.query.filter_by(token=token_string).first()
        
        if not token or not token.is_valid():
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        # Update user email
        user = User.query.get(token.user_id)
        old_email = user.email
        user.email = token.email
        user.email_verified = True
        
        # Mark token as used
        token.mark_used()
        
        db.session.commit()
        
        # Log the change
        AuditLogger.log_email_change(user.id, old_email, token.email)
        
        # Send notification to old email
        try:
            EmailService.send_email_changed_notification(user, old_email)
        except:
            pass
        
        return jsonify({
            'message': 'Email verified and updated successfully',
            'user': user_schema.dump(user)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/password-status', methods=['GET'])
@jwt_required()
def password_status():
    """Check password expiration status (HIPAA compliance)."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        from datetime import datetime
        days_until_expiry = None
        is_expired = user.is_password_expired()
        
        if user.password_expires_at and not is_expired:
            delta = user.password_expires_at - datetime.utcnow()
            days_until_expiry = delta.days
        
        return jsonify({
            'password_expired': is_expired,
            'password_expires_at': user.password_expires_at.isoformat() if user.password_expires_at else None,
            'days_until_expiry': days_until_expiry,
            'password_changed_at': user.password_changed_at.isoformat() if user.password_changed_at else None,
            'require_password_change': user.require_password_change,
            'warning': 'Password expires soon - please change it' if days_until_expiry and days_until_expiry <= 7 else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


