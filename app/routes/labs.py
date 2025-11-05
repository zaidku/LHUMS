"""Lab management routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app import db
from app.models.user import User
from app.models.lab import Lab, LabMembership
from app.schemas import (
    lab_schema,
    labs_schema,
    lab_create_schema,
    lab_membership_schema,
    lab_memberships_schema,
    add_member_schema
)
from app.utils.decorators import admin_required, lab_admin_required, require_lab_access
from app.utils.tenant_context import get_current_user_labs, verify_lab_access

labs_bp = Blueprint('labs', __name__)


@labs_bp.route('', methods=['GET'])
@jwt_required()
def list_labs():
    """List all labs accessible to current user (data isolation)."""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # System admins can see all labs
        if user and user.is_admin:
            labs = Lab.query.filter_by(is_active=True).all()
        else:
            # Regular users only see their labs (data isolation)
            user_lab_ids = get_current_user_labs()
            labs = Lab.query.filter(
                Lab.id.in_(user_lab_ids),
                Lab.is_active == True
            ).all()
        
        return jsonify({
            'labs': labs_schema.dump(labs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@labs_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_lab():
    """Create a new lab (admin only)."""
    try:
        # Validate request data
        data = lab_create_schema.load(request.get_json())
        
        # Create new lab
        lab = Lab(
            name=data['name'],
            code=data['code'],
            description=data.get('description')
        )
        
        db.session.add(lab)
        db.session.commit()
        
        return jsonify({
            'message': 'Lab created successfully',
            'lab': lab_schema.dump(lab)
        }), 201
        
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labs_bp.route('/<int:lab_id>', methods=['GET'])
@jwt_required()
@require_lab_access
def get_lab(lab_id):
    """Get lab by ID (data isolation - user must be member)."""
    try:
        lab = Lab.query.get(lab_id)
        if not lab:
            return jsonify({'error': 'Lab not found'}), 404
        
        return jsonify({
            'lab': lab_schema.dump(lab)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@labs_bp.route('/<int:lab_id>', methods=['PUT', 'PATCH'])
@jwt_required()
@admin_required
def update_lab(lab_id):
    """Update lab (admin only)."""
    try:
        lab = Lab.query.get(lab_id)
        if not lab:
            return jsonify({'error': 'Lab not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            lab.name = data['name']
        if 'description' in data:
            lab.description = data['description']
        if 'is_active' in data:
            lab.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lab updated successfully',
            'lab': lab_schema.dump(lab)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labs_bp.route('/<int:lab_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_lab(lab_id):
    """Delete lab (admin only)."""
    try:
        lab = Lab.query.get(lab_id)
        if not lab:
            return jsonify({'error': 'Lab not found'}), 404
        
        db.session.delete(lab)
        db.session.commit()
        
        return jsonify({
            'message': 'Lab deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labs_bp.route('/<int:lab_id>/members', methods=['GET'])
@jwt_required()
@require_lab_access
def get_lab_members(lab_id):
    """Get all members of a lab (data isolation - user must be member)."""
    try:
        lab = Lab.query.get(lab_id)
        if not lab:
            return jsonify({'error': 'Lab not found'}), 404
        
        return jsonify({
            'members': lab_memberships_schema.dump(lab.memberships)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@labs_bp.route('/<int:lab_id>/members', methods=['POST'])
@jwt_required()
@lab_admin_required
def add_lab_member(lab_id):
    """Add a member to a lab (lab admin or system admin only)."""
    try:
        lab = Lab.query.get(lab_id)
        if not lab:
            return jsonify({'error': 'Lab not found'}), 404
        
        # Validate request data
        data = add_member_schema.load(request.get_json())
        
        # Check if user exists
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if membership already exists
        existing = LabMembership.query.filter_by(
            user_id=data['user_id'],
            lab_id=lab_id
        ).first()
        
        if existing:
            return jsonify({'error': 'User is already a member of this lab'}), 400
        
        # Create new membership
        membership = LabMembership(
            user_id=data['user_id'],
            lab_id=lab_id,
            role=data.get('role', 'member')
        )
        
        db.session.add(membership)
        db.session.commit()
        
        return jsonify({
            'message': 'Member added successfully',
            'membership': lab_membership_schema.dump(membership)
        }), 201
        
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labs_bp.route('/<int:lab_id>/members/<int:user_id>', methods=['DELETE'])
@jwt_required()
@lab_admin_required
def remove_lab_member(lab_id, user_id):
    """Remove a member from a lab (lab admin or system admin only)."""
    try:
        membership = LabMembership.query.filter_by(
            user_id=user_id,
            lab_id=lab_id
        ).first()
        
        if not membership:
            return jsonify({'error': 'Membership not found'}), 404
        
        db.session.delete(membership)
        db.session.commit()
        
        return jsonify({
            'message': 'Member removed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@labs_bp.route('/<int:lab_id>/members/<int:user_id>/role', methods=['PATCH'])
@jwt_required()
@lab_admin_required
def update_member_role(lab_id, user_id):
    """Update a member's role in a lab (lab admin or system admin only)."""
    try:
        membership = LabMembership.query.filter_by(
            user_id=user_id,
            lab_id=lab_id
        ).first()
        
        if not membership:
            return jsonify({'error': 'Membership not found'}), 404
        
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['admin', 'member', 'viewer']:
            return jsonify({'error': 'Invalid role'}), 400
        
        membership.role = new_role
        db.session.commit()
        
        return jsonify({
            'message': 'Role updated successfully',
            'membership': lab_membership_schema.dump(membership)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
