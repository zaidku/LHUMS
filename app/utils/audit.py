"""Audit logging utility."""
from app import db
from app.models.token import AuditLog
from flask import request
import json
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """Utility for creating audit log entries."""
    
    @staticmethod
    def log(user_id, action, resource_type=None, resource_id=None, 
            details=None, success=True):
        """Create an audit log entry.
        
        Args:
            user_id: ID of the user performing the action (can be None)
            action: Action type (use AuditLog.ACTION_* constants)
            resource_type: Type of resource affected (user, lab, etc.)
            resource_id: ID of the affected resource
            details: Additional details (dict will be converted to JSON)
            success: Whether the action was successful
        """
        try:
            ip_address = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent', '')[:255] if request else None
            
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=json.dumps(details) if details else None,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info(f"Audit log: {action} by user_id={user_id} success={success}")
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            # Don't fail the main operation if audit logging fails
            try:
                db.session.rollback()
            except:
                pass
    
    @staticmethod
    def log_login(user_id, success=True):
        """Log a login attempt."""
        AuditLogger.log(user_id, AuditLog.ACTION_LOGIN if success else AuditLog.ACTION_FAILED_LOGIN, 
                       success=success)
    
    @staticmethod
    def log_logout(user_id):
        """Log a logout."""
        AuditLogger.log(user_id, AuditLog.ACTION_LOGOUT)
    
    @staticmethod
    def log_registration(user_id):
        """Log a user registration."""
        AuditLogger.log(user_id, AuditLog.ACTION_REGISTER)
    
    @staticmethod
    def log_password_reset_request(user_id, email):
        """Log a password reset request."""
        AuditLogger.log(user_id, AuditLog.ACTION_PASSWORD_RESET_REQUEST,
                       details={'email': email})
    
    @staticmethod
    def log_password_reset(user_id):
        """Log a password reset."""
        AuditLogger.log(user_id, AuditLog.ACTION_PASSWORD_RESET)
    
    @staticmethod
    def log_password_change(user_id):
        """Log a password change."""
        AuditLogger.log(user_id, AuditLog.ACTION_PASSWORD_CHANGE)
    
    @staticmethod
    def log_email_change(user_id, old_email, new_email):
        """Log an email change."""
        AuditLogger.log(user_id, AuditLog.ACTION_EMAIL_CHANGE,
                       details={'old_email': old_email, 'new_email': new_email})
    
    @staticmethod
    def log_profile_update(user_id):
        """Log a profile update."""
        AuditLogger.log(user_id, AuditLog.ACTION_PROFILE_UPDATE, 
                       resource_type='user', resource_id=user_id)
    
    @staticmethod
    def log_user_delete(admin_id, deleted_user_id):
        """Log a user deletion."""
        AuditLogger.log(admin_id, AuditLog.ACTION_USER_DELETE,
                       resource_type='user', resource_id=deleted_user_id)
    
    @staticmethod
    def log_lab_create(user_id, lab_id):
        """Log a lab creation."""
        AuditLogger.log(user_id, AuditLog.ACTION_LAB_CREATE,
                       resource_type='lab', resource_id=lab_id)
    
    @staticmethod
    def log_lab_update(user_id, lab_id):
        """Log a lab update."""
        AuditLogger.log(user_id, AuditLog.ACTION_LAB_UPDATE,
                       resource_type='lab', resource_id=lab_id)
    
    @staticmethod
    def log_lab_delete(user_id, lab_id):
        """Log a lab deletion."""
        AuditLogger.log(user_id, AuditLog.ACTION_LAB_DELETE,
                       resource_type='lab', resource_id=lab_id)
    
    @staticmethod
    def log_member_add(user_id, lab_id, added_user_id):
        """Log adding a member to a lab."""
        AuditLogger.log(user_id, AuditLog.ACTION_MEMBER_ADD,
                       resource_type='lab', resource_id=lab_id,
                       details={'added_user_id': added_user_id})
    
    @staticmethod
    def log_member_remove(user_id, lab_id, removed_user_id):
        """Log removing a member from a lab."""
        AuditLogger.log(user_id, AuditLog.ACTION_MEMBER_REMOVE,
                       resource_type='lab', resource_id=lab_id,
                       details={'removed_user_id': removed_user_id})
    
    @staticmethod
    def log_role_update(user_id, lab_id, target_user_id, new_role):
        """Log updating a user's role in a lab."""
        AuditLogger.log(user_id, AuditLog.ACTION_ROLE_UPDATE,
                       resource_type='lab', resource_id=lab_id,
                       details={'target_user_id': target_user_id, 'new_role': new_role})
