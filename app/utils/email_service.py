"""Email service for sending notifications."""
from flask import render_template_string
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    @staticmethod
    def send_email(to, subject, body_html, body_text=None):
        """Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content (optional)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            msg = Message(
                subject=subject,
                recipients=[to] if isinstance(to, str) else to,
                html=body_html,
                body=body_text or body_html
            )
            mail.send(msg)
            logger.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email to new user.
        
        Args:
            user: User object
        """
        subject = "Welcome to UMS!"
        body = f"""
        <html>
        <body>
            <h2>Welcome to User Management Service!</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Your account has been successfully created.</p>
            <p><strong>Username:</strong> {user.username}</p>
            <p><strong>Email:</strong> {user.email}</p>
            <p>Thank you for registering!</p>
            <br>
            <p>Best regards,<br>UMS Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, body)
    
    @staticmethod
    def send_password_reset_email(user, token):
        """Send password reset email.
        
        Args:
            user: User object
            token: Password reset token string
        """
        # In production, this should be your actual domain
        reset_url = f"http://localhost:5000/reset-password?token={token}"
        
        subject = "Password Reset Request"
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>You requested to reset your password. Click the link below to reset it:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>UMS Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, body)
    
    @staticmethod
    def send_password_changed_email(user):
        """Send notification that password was changed.
        
        Args:
            user: User object
        """
        subject = "Password Changed"
        body = f"""
        <html>
        <body>
            <h2>Password Changed</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Your password was successfully changed.</p>
            <p>If you didn't make this change, please contact support immediately.</p>
            <br>
            <p>Best regards,<br>UMS Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, body)
    
    @staticmethod
    def send_email_verification(user, token, new_email):
        """Send email verification link.
        
        Args:
            user: User object
            token: Verification token string
            new_email: New email address to verify
        """
        verify_url = f"http://localhost:5000/verify-email?token={token}"
        
        subject = "Verify Your Email Address"
        body = f"""
        <html>
        <body>
            <h2>Email Verification</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verify_url}">{verify_url}</a></p>
            <p>This link will expire in 48 hours.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>UMS Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(new_email, subject, body)
    
    @staticmethod
    def send_email_changed_notification(user, old_email):
        """Send notification to old email that email was changed.
        
        Args:
            user: User object
            old_email: Previous email address
        """
        subject = "Email Address Changed"
        body = f"""
        <html>
        <body>
            <h2>Email Address Changed</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Your email address was changed from <strong>{old_email}</strong> to <strong>{user.email}</strong>.</p>
            <p>If you didn't make this change, please contact support immediately.</p>
            <br>
            <p>Best regards,<br>UMS Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(old_email, subject, body)
    
    @staticmethod
    def send_account_locked_email(user):
        """Send notification that account was locked.
        
        Args:
            user: User object
        """
        subject = "Account Locked"
        body = f"""
        <html>
        <body>
            <h2>Account Locked</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>Your account has been locked due to multiple failed login attempts.</p>
            <p>It will automatically unlock in 30 minutes, or you can reset your password.</p>
            <p>If you didn't attempt to login, please contact support immediately.</p>
            <br>
            <p>Best regards,<br>UMS Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, body)
    
    @staticmethod
    def send_login_alert(user, ip_address, user_agent):
        """Send alert for new login from unfamiliar location.
        
        Args:
            user: User object
            ip_address: IP address of login
            user_agent: User agent string
        """
        subject = "New Login Alert"
        body = f"""
        <html>
        <body>
            <h2>New Login Detected</h2>
            <p>Hi {user.first_name or user.username},</p>
            <p>A new login to your account was detected:</p>
            <ul>
                <li><strong>IP Address:</strong> {ip_address}</li>
                <li><strong>Device:</strong> {user_agent}</li>
            </ul>
            <p>If this was you, you can ignore this email.</p>
            <p>If you don't recognize this activity, please change your password immediately.</p>
            <br>
            <p>Best regards,<br>UMS Team</p>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, body)
