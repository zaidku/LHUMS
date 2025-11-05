"""User serialization schemas."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app import ma
from app.models.user import User


class UserSchema(ma.SQLAlchemyAutoSchema):
    """User schema for serialization."""
    
    class Meta:
        model = User
        load_instance = True
        exclude = ('password_hash',)
        dump_only = ('id', 'created_at', 'updated_at')
    
    email = fields.Email(required=True)
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    first_name = fields.String(validate=validate.Length(max=50))
    last_name = fields.String(validate=validate.Length(max=50))


class UserRegistrationSchema(Schema):
    """Schema for user registration."""
    
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6), load_only=True)
    first_name = fields.String(validate=validate.Length(max=50))
    last_name = fields.String(validate=validate.Length(max=50))
    
    @validates('username')
    def validate_username(self, value):
        """Check if username already exists."""
        if User.query.filter_by(username=value).first():
            raise ValidationError('Username already exists.')
    
    @validates('email')
    def validate_email(self, value):
        """Check if email already exists."""
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already exists.')


class UserLoginSchema(Schema):
    """Schema for user login."""
    
    username = fields.String(required=True)
    password = fields.String(required=True, load_only=True)


class UserUpdateSchema(Schema):
    """Schema for user profile update."""
    
    email = fields.Email()
    first_name = fields.String(validate=validate.Length(max=50))
    last_name = fields.String(validate=validate.Length(max=50))
    is_active = fields.Boolean()
    
    @validates('email')
    def validate_email(self, value):
        """Check if email is already in use by another user."""
        from flask import g
        existing_user = User.query.filter_by(email=value).first()
        if existing_user and existing_user.id != g.get('user_id'):
            raise ValidationError('Email already in use.')


# Schema instances
user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_registration_schema = UserRegistrationSchema()
user_login_schema = UserLoginSchema()
user_update_schema = UserUpdateSchema()
