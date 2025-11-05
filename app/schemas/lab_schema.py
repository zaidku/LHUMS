"""Lab serialization schemas."""
from marshmallow import Schema, fields, validate, validates, ValidationError
from app import ma
from app.models.lab import Lab, LabMembership


class LabSchema(ma.SQLAlchemyAutoSchema):
    """Lab schema for serialization."""
    
    class Meta:
        model = Lab
        load_instance = True
        dump_only = ('id', 'created_at', 'updated_at')
    
    name = fields.String(required=True, validate=validate.Length(min=3, max=100))
    code = fields.String(required=True, validate=validate.Length(min=2, max=20))
    description = fields.String()


class LabMembershipSchema(ma.SQLAlchemyAutoSchema):
    """Lab membership schema for serialization."""
    
    class Meta:
        model = LabMembership
        load_instance = True
        dump_only = ('id', 'joined_at')
    
    user_id = fields.Integer(required=True)
    lab_id = fields.Integer(required=True)
    role = fields.String(validate=validate.OneOf(['admin', 'member', 'viewer']))
    
    # Nested fields for detailed responses
    user = fields.Nested('UserSchema', dump_only=True, exclude=('lab_memberships',))
    lab = fields.Nested('LabSchema', dump_only=True, exclude=('memberships',))


class LabCreateSchema(Schema):
    """Schema for lab creation."""
    
    name = fields.String(required=True, validate=validate.Length(min=3, max=100))
    code = fields.String(required=True, validate=validate.Length(min=2, max=20))
    description = fields.String()
    
    @validates('code')
    def validate_code(self, value):
        """Check if lab code already exists."""
        if Lab.query.filter_by(code=value).first():
            raise ValidationError('Lab code already exists.')
    
    @validates('name')
    def validate_name(self, value):
        """Check if lab name already exists."""
        if Lab.query.filter_by(name=value).first():
            raise ValidationError('Lab name already exists.')


class AddMemberSchema(Schema):
    """Schema for adding a member to a lab."""
    
    user_id = fields.Integer(required=True)
    role = fields.String(validate=validate.OneOf(['admin', 'member', 'viewer']), missing='member')


# Schema instances
lab_schema = LabSchema()
labs_schema = LabSchema(many=True)
lab_create_schema = LabCreateSchema()
lab_membership_schema = LabMembershipSchema()
lab_memberships_schema = LabMembershipSchema(many=True)
add_member_schema = AddMemberSchema()
