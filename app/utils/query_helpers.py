"""Query helpers for data isolation and multi-tenancy."""
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.utils.tenant_context import get_current_user_labs


def scope_to_user_labs(query, model, lab_field='lab_id'):
    """Automatically filter query to only include data from user's labs.
    
    This helper ensures data isolation by restricting queries to only
    return records that belong to labs the current user has access to.
    
    Args:
        query: SQLAlchemy query object
        model: The model class being queried
        lab_field: Name of the lab_id field (default: 'lab_id')
        
    Returns:
        Filtered query scoped to user's accessible labs
        
    Example:
        # Instead of:
        patients = Patient.query.all()  # Returns ALL patients across ALL labs
        
        # Use:
        patients = scope_to_user_labs(Patient.query, Patient).all()  # Only user's labs
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # System admins can see all data
    if user and user.is_admin:
        return query
    
    # Regular users only see data from their labs
    user_lab_ids = get_current_user_labs()
    
    # Get the lab_id field from the model
    lab_column = getattr(model, lab_field)
    
    # Filter query to only include records from user's labs
    return query.filter(lab_column.in_(user_lab_ids))


def verify_record_access(record, lab_field='lab_id'):
    """Verify current user has access to a specific record.
    
    Args:
        record: Database record to check access for
        lab_field: Name of the lab_id field (default: 'lab_id')
        
    Returns:
        bool: True if user has access, False otherwise
        
    Example:
        patient = Patient.query.get(patient_id)
        if not verify_record_access(patient):
            abort(403)
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # System admins can access all records
    if user and user.is_admin:
        return True
    
    # Get lab_id from the record
    record_lab_id = getattr(record, lab_field, None)
    
    if not record_lab_id:
        return False
    
    # Check if user has access to this lab
    user_lab_ids = get_current_user_labs()
    return record_lab_id in user_lab_ids


class LabScopedQuery:
    """Mixin class to automatically scope queries to user's labs.
    
    Usage:
        class Patient(db.Model, LabScopedQuery):
            id = db.Column(db.Integer, primary_key=True)
            lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False)
            name = db.Column(db.String(100))
            
        # Now queries are automatically scoped
        patients = Patient.scoped_query().all()  # Only from user's labs
    """
    
    @classmethod
    def scoped_query(cls, lab_field='lab_id'):
        """Get a query scoped to current user's labs."""
        from app import db
        return scope_to_user_labs(db.session.query(cls), cls, lab_field)
    
    def verify_access(self, lab_field='lab_id'):
        """Verify current user has access to this record."""
        return verify_record_access(self, lab_field)
