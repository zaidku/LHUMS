"""Attribute schemas for serialization and validation."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app import ma
from app.models.attribute import Attribute, RoleAttribute, UserLabAttribute


class AttributeSchema(ma.SQLAlchemyAutoSchema):
    """Schema for Attribute model."""
    
    class Meta:
        model = Attribute
        load_instance = True
        dump_only = ('id', 'created_at')
    
    name = fields.String(
        required=True,
        validate=[
            validate.Length(min=3, max=100),
            validate.Regexp(r'^[a-z]+(\.[a-z_]+)*$', error='Name must be lowercase with dots (e.g., lab.patient.read)')
        ]
    )
    description = fields.String(validate=validate.Length(max=500))
    category = fields.String(
        required=True,
        validate=validate.OneOf(['lab', 'system', 'billing', 'reports', 'admin'])
    )
    
    @validates('name')
    def validate_name(self, value):
        """Validate attribute name format."""
        if not value:
            raise ValidationError('Attribute name is required')
        
        # Check format: category.resource.action
        parts = value.split('.')
        if len(parts) < 2:
            raise ValidationError('Attribute name must have at least 2 parts (e.g., lab.patient)')
        
        if len(parts) > 4:
            raise ValidationError('Attribute name can have at most 4 parts')
        
        # Validate each part
        for part in parts:
            if not part.replace('_', '').isalpha():
                raise ValidationError('Each part of attribute name must contain only letters and underscores')


class RoleAttributeSchema(ma.SQLAlchemyAutoSchema):
    """Schema for RoleAttribute model."""
    
    class Meta:
        model = RoleAttribute
        load_instance = True
        dump_only = ('id', 'granted_by', 'granted_at')
    
    role_name = fields.String(
        required=True,
        validate=validate.OneOf(['admin', 'member', 'viewer'])
    )
    
    # Nested fields for display
    attribute = fields.Nested(AttributeSchema, dump_only=True)


class UserLabAttributeSchema(ma.SQLAlchemyAutoSchema):
    """Schema for UserLabAttribute model."""
    
    class Meta:
        model = UserLabAttribute
        load_instance = True
        dump_only = ('id', 'granted_by', 'granted_at')
    
    # Computed fields
    is_expired = fields.Method('get_is_expired', dump_only=True)
    is_valid = fields.Method('get_is_valid', dump_only=True)
    
    # Nested fields for display
    attribute = fields.Nested(AttributeSchema, dump_only=True)
    
    def get_is_expired(self, obj):
        """Check if the attribute grant has expired."""
        return obj.is_expired() if hasattr(obj, 'is_expired') else False
    
    def get_is_valid(self, obj):
        """Check if the attribute grant is currently valid."""
        return obj.is_valid() if hasattr(obj, 'is_valid') else False


class UserAttributesResponseSchema(Schema):
    """Schema for user attributes response (used in authorization)."""
    
    user_id = fields.Integer()
    username = fields.String()
    lab_id = fields.Integer()
    attributes = fields.List(fields.String())
    roles = fields.List(fields.String())
    is_admin = fields.Boolean()
    
    # Additional context
    lab_name = fields.String()
    lab_code = fields.String()
    membership_role = fields.String()


class AttributeCheckRequestSchema(Schema):
    """Schema for attribute check requests."""
    
    user_id = fields.Integer(required=True)
    lab_id = fields.Integer(required=True)
    required_attributes = fields.List(
        fields.String(),
        required=True,
        validate=validate.Length(min=1, max=10)
    )
    
    @validates('required_attributes')
    def validate_required_attributes(self, value):
        """Validate required attributes format."""
        for attr in value:
            if not attr or not isinstance(attr, str):
                raise ValidationError('All attributes must be non-empty strings')
            
            if not attr.count('.') >= 1:
                raise ValidationError('Attributes must be in format: category.resource.action')


class AttributeCheckResponseSchema(Schema):
    """Schema for attribute check responses."""
    
    user_id = fields.Integer()
    lab_id = fields.Integer()
    has_access = fields.Boolean()
    granted_attributes = fields.List(fields.String())
    missing_attributes = fields.List(fields.String())
    
    # Additional context
    user_roles = fields.List(fields.String())
    is_lab_admin = fields.Boolean()
    is_system_admin = fields.Boolean()


# Create schema instances
attribute_schema = AttributeSchema()
attributes_schema = AttributeSchema(many=True)
role_attribute_schema = RoleAttributeSchema()
user_lab_attribute_schema = UserLabAttributeSchema()
user_attributes_response_schema = UserAttributesResponseSchema()
attribute_check_request_schema = AttributeCheckRequestSchema()
attribute_check_response_schema = AttributeCheckResponseSchema()