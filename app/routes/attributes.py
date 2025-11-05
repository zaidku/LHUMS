"""Attribute management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Lab, LabMembership, Attribute, RoleAttribute, UserLabAttribute
from app.utils.decorators import admin_required, lab_admin_required
from app.utils.audit import log_audit_event
from app.schemas import AttributeSchema, RoleAttributeSchema, UserLabAttributeSchema
from marshmallow import ValidationError

attributes_bp = Blueprint('attributes', __name__)
attribute_schema = AttributeSchema()
attributes_schema = AttributeSchema(many=True)
role_attribute_schema = RoleAttributeSchema()
user_lab_attribute_schema = UserLabAttributeSchema()


@attributes_bp.route('/attributes', methods=['GET'])
@jwt_required()
def list_attributes():
    """List all system attributes."""
    category = request.args.get('category')
    
    query = Attribute.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    
    attributes = query.order_by(Attribute.category, Attribute.name).all()
    return jsonify({
        'attributes': attributes_schema.dump(attributes),
        'total': len(attributes)
    }), 200


@attributes_bp.route('/attributes', methods=['POST'])
@jwt_required()
@admin_required
def create_attribute():
    """Create a new system attribute (system admin only)."""
    try:
        data = attribute_schema.load(request.get_json())
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.messages}), 400
    
    # Check if attribute already exists
    if Attribute.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Attribute already exists'}), 409
    
    attribute = Attribute(**data)
    db.session.add(attribute)
    db.session.commit()
    
    # Log audit event
    log_audit_event(
        user_id=get_jwt_identity(),
        action='attribute_created',
        resource_type='attribute',
        resource_id=attribute.id,
        details={'name': attribute.name, 'category': attribute.category}
    )
    
    return jsonify({
        'message': 'Attribute created successfully',
        'attribute': attribute_schema.dump(attribute)
    }), 201


@attributes_bp.route('/labs/<int:lab_id>/role-attributes', methods=['GET'])
@jwt_required()
@lab_admin_required
def list_lab_role_attributes(lab_id):
    """List role-attribute mappings for a lab."""
    lab = Lab.query.get_or_404(lab_id)
    
    # Get role-attributes for this lab and system-wide
    role_attributes = RoleAttribute.query.filter(
        (RoleAttribute.lab_id == lab_id) | (RoleAttribute.lab_id.is_(None))
    ).join(Attribute).filter(Attribute.is_active == True).all()
    
    # Group by role
    roles_data = {}
    for ra in role_attributes:
        if ra.role_name not in roles_data:
            roles_data[ra.role_name] = {
                'role': ra.role_name,
                'attributes': []
            }
        
        roles_data[ra.role_name]['attributes'].append({
            'id': ra.attribute.id,
            'name': ra.attribute.name,
            'description': ra.attribute.description,
            'category': ra.attribute.category,
            'scope': 'lab' if ra.lab_id else 'system',
            'granted_at': ra.granted_at.isoformat()
        })
    
    return jsonify({
        'lab_id': lab_id,
        'lab_name': lab.name,
        'roles': list(roles_data.values())
    }), 200


@attributes_bp.route('/labs/<int:lab_id>/role-attributes', methods=['POST'])
@jwt_required()
@lab_admin_required
def assign_role_attribute(lab_id):
    """Assign an attribute to a role within a lab."""
    lab = Lab.query.get_or_404(lab_id)
    
    try:
        data = request.get_json()
        role_name = data.get('role_name')
        attribute_id = data.get('attribute_id')
        
        if not role_name or not attribute_id:
            return jsonify({'error': 'role_name and attribute_id are required'}), 400
        
        if role_name not in ['admin', 'member', 'viewer']:
            return jsonify({'error': 'Invalid role_name. Must be admin, member, or viewer'}), 400
        
    except Exception as e:
        return jsonify({'error': 'Invalid request data'}), 400
    
    # Check if attribute exists and is active
    attribute = Attribute.query.filter_by(id=attribute_id, is_active=True).first()
    if not attribute:
        return jsonify({'error': 'Attribute not found or inactive'}), 404
    
    # Check if mapping already exists
    existing = RoleAttribute.query.filter_by(
        role_name=role_name,
        attribute_id=attribute_id,
        lab_id=lab_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Role-attribute mapping already exists'}), 409
    
    # Create new mapping
    role_attribute = RoleAttribute(
        role_name=role_name,
        attribute_id=attribute_id,
        lab_id=lab_id,
        granted_by=get_jwt_identity()
    )
    
    db.session.add(role_attribute)
    db.session.commit()
    
    # Log audit event
    log_audit_event(
        user_id=get_jwt_identity(),
        action='role_attribute_assigned',
        resource_type='lab',
        resource_id=lab_id,
        details={
            'role': role_name,
            'attribute': attribute.name,
            'attribute_id': attribute_id
        }
    )
    
    return jsonify({
        'message': 'Attribute assigned to role successfully',
        'role_attribute': {
            'role_name': role_name,
            'attribute_name': attribute.name,
            'lab_id': lab_id
        }
    }), 201


@attributes_bp.route('/labs/<int:lab_id>/role-attributes/<int:role_attribute_id>', methods=['DELETE'])
@jwt_required()
@lab_admin_required
def remove_role_attribute(lab_id, role_attribute_id):
    """Remove an attribute from a role within a lab."""
    lab = Lab.query.get_or_404(lab_id)
    
    role_attribute = RoleAttribute.query.filter_by(
        id=role_attribute_id,
        lab_id=lab_id
    ).first()
    
    if not role_attribute:
        return jsonify({'error': 'Role-attribute mapping not found'}), 404
    
    # Store details for audit log
    details = {
        'role': role_attribute.role_name,
        'attribute': role_attribute.attribute.name,
        'attribute_id': role_attribute.attribute_id
    }
    
    db.session.delete(role_attribute)
    db.session.commit()
    
    # Log audit event
    log_audit_event(
        user_id=get_jwt_identity(),
        action='role_attribute_removed',
        resource_type='lab',
        resource_id=lab_id,
        details=details
    )
    
    return jsonify({'message': 'Attribute removed from role successfully'}), 200


@attributes_bp.route('/labs/<int:lab_id>/user-attributes', methods=['GET'])
@jwt_required()
@lab_admin_required
def list_user_attributes(lab_id):
    """List user-specific attributes for a lab."""
    lab = Lab.query.get_or_404(lab_id)
    
    user_attributes = UserLabAttribute.query.filter_by(
        lab_id=lab_id,
        is_active=True
    ).join(User).join(Attribute).filter(
        Attribute.is_active == True
    ).all()
    
    # Group by user
    users_data = {}
    for ua in user_attributes:
        if ua.user_id not in users_data:
            users_data[ua.user_id] = {
                'user_id': ua.user_id,
                'username': ua.user.username,
                'email': ua.user.email,
                'attributes': []
            }
        
        users_data[ua.user_id]['attributes'].append({
            'id': ua.id,
            'attribute_id': ua.attribute_id,
            'attribute_name': ua.attribute.name,
            'description': ua.attribute.description,
            'granted_at': ua.granted_at.isoformat(),
            'expires_at': ua.expires_at.isoformat() if ua.expires_at else None,
            'is_expired': ua.is_expired()
        })
    
    return jsonify({
        'lab_id': lab_id,
        'lab_name': lab.name,
        'users': list(users_data.values())
    }), 200


@attributes_bp.route('/labs/<int:lab_id>/user-attributes', methods=['POST'])
@jwt_required()
@lab_admin_required
def grant_user_attribute(lab_id):
    """Grant a specific attribute to a user within a lab."""
    lab = Lab.query.get_or_404(lab_id)
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        attribute_id = data.get('attribute_id')
        expires_at = data.get('expires_at')  # Optional
        
        if not user_id or not attribute_id:
            return jsonify({'error': 'user_id and attribute_id are required'}), 400
        
    except Exception as e:
        return jsonify({'error': 'Invalid request data'}), 400
    
    # Check if user is a member of this lab
    membership = LabMembership.query.filter_by(
        user_id=user_id,
        lab_id=lab_id,
        is_active=True
    ).first()
    
    if not membership:
        return jsonify({'error': 'User is not a member of this lab'}), 404
    
    # Check if attribute exists and is active
    attribute = Attribute.query.filter_by(id=attribute_id, is_active=True).first()
    if not attribute:
        return jsonify({'error': 'Attribute not found or inactive'}), 404
    
    # Check if user already has this attribute
    existing = UserLabAttribute.query.filter_by(
        user_id=user_id,
        lab_id=lab_id,
        attribute_id=attribute_id
    ).first()
    
    if existing:
        if existing.is_active:
            return jsonify({'error': 'User already has this attribute'}), 409
        else:
            # Reactivate existing grant
            existing.is_active = True
            existing.granted_by = get_jwt_identity()
            existing.granted_at = db.func.now()
            if expires_at:
                from datetime import datetime
                existing.expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            db.session.commit()
            
            return jsonify({
                'message': 'User attribute reactivated successfully',
                'user_attribute': user_lab_attribute_schema.dump(existing)
            }), 200
    
    # Create new user attribute grant
    user_attribute = UserLabAttribute(
        user_id=user_id,
        lab_id=lab_id,
        attribute_id=attribute_id,
        granted_by=get_jwt_identity()
    )
    
    if expires_at:
        from datetime import datetime
        user_attribute.expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    
    db.session.add(user_attribute)
    db.session.commit()
    
    # Log audit event
    log_audit_event(
        user_id=get_jwt_identity(),
        action='user_attribute_granted',
        resource_type='lab',
        resource_id=lab_id,
        details={
            'target_user_id': user_id,
            'attribute': attribute.name,
            'attribute_id': attribute_id,
            'expires_at': expires_at
        }
    )
    
    return jsonify({
        'message': 'Attribute granted to user successfully',
        'user_attribute': user_lab_attribute_schema.dump(user_attribute)
    }), 201


@attributes_bp.route('/labs/<int:lab_id>/user-attributes/<int:user_attribute_id>', methods=['DELETE'])
@jwt_required()
@lab_admin_required
def revoke_user_attribute(lab_id, user_attribute_id):
    """Revoke a user-specific attribute within a lab."""
    lab = Lab.query.get_or_404(lab_id)
    
    user_attribute = UserLabAttribute.query.filter_by(
        id=user_attribute_id,
        lab_id=lab_id
    ).first()
    
    if not user_attribute:
        return jsonify({'error': 'User attribute not found'}), 404
    
    # Store details for audit log
    details = {
        'target_user_id': user_attribute.user_id,
        'attribute': user_attribute.attribute.name,
        'attribute_id': user_attribute.attribute_id
    }
    
    # Soft delete - mark as inactive
    user_attribute.is_active = False
    db.session.commit()
    
    # Log audit event
    log_audit_event(
        user_id=get_jwt_identity(),
        action='user_attribute_revoked',
        resource_type='lab',
        resource_id=lab_id,
        details=details
    )
    
    return jsonify({'message': 'User attribute revoked successfully'}), 200