# Multi-Tenant Architecture - Data Isolation Guide

## Current Multi-Tenant Support ✅

### Lab-Based Tenancy
- **Labs** act as tenants (isolated environments)
- **LabMembership** links users to labs with roles
- **Role-Based Access Control** per lab (admin, member, viewer)

### Database Schema
```
┌─────────┐       ┌──────────────────┐       ┌──────┐
│  User   │──────▶│ LabMembership    │◀──────│ Lab  │
├─────────┤       ├──────────────────┤       ├──────┤
│ id      │       │ id               │       │ id   │
│ username│       │ user_id          │       │ name │
│ email   │       │ lab_id           │       │ code │
│ is_admin│       │ role (admin/etc) │       └──────┘
└─────────┘       │ is_active        │
                  └──────────────────┘
```

## ⚠️ DATA ISOLATION - IMPLEMENTATION NEEDED

### Critical Issue
**Your current system does NOT isolate data by lab!**

When you add lab-specific data (e.g., patients, tests, records), you need to:
1. Add `lab_id` foreign key to ALL lab-specific tables
2. Always filter queries by current user's lab
3. Prevent cross-lab data access

## Implementation Guide

### 1. Add Lab Context Middleware

Create `app/utils/tenant_context.py`:

```python
"""Tenant context for multi-lab data isolation."""
from flask import g
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.models.lab import LabMembership


def get_current_user_labs():
    """Get all lab IDs the current user has access to."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # System admins can access all labs
    if user and user.is_admin:
        from app.models.lab import Lab
        return [lab.id for lab in Lab.query.all()]
    
    # Regular users can only access their labs
    memberships = LabMembership.query.filter_by(
        user_id=user_id,
        is_active=True
    ).all()
    
    return [m.lab_id for m in memberships]


def get_current_lab():
    """Get the current lab from request context."""
    return g.get('current_lab_id')


def set_current_lab(lab_id):
    """Set the current lab in request context."""
    g.current_lab_id = lab_id


def verify_lab_access(lab_id):
    """Verify current user has access to lab."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # System admins can access all labs
    if user and user.is_admin:
        return True
    
    # Check membership
    membership = LabMembership.query.filter_by(
        user_id=user_id,
        lab_id=lab_id,
        is_active=True
    ).first()
    
    return membership is not None
```

### 2. Create Decorator for Lab Access

Add to `app/utils/decorators.py`:

```python
def require_lab_access(fn):
    """Decorator to verify user has access to requested lab."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        lab_id = kwargs.get('lab_id') or request.args.get('lab_id') or request.json.get('lab_id')
        
        if not lab_id:
            return jsonify({'error': 'Lab ID required'}), 400
        
        from app.utils.tenant_context import verify_lab_access
        if not verify_lab_access(lab_id):
            return jsonify({'error': 'Access to this lab is forbidden'}), 403
        
        # Store lab_id in context for use in views
        from app.utils.tenant_context import set_current_lab
        set_current_lab(lab_id)
        
        return fn(*args, **kwargs)
    
    return wrapper
```

### 3. Example: Lab-Specific Data Model

When you add lab-specific data (e.g., patients):

```python
class Patient(db.Model):
    """Patient record - belongs to a lab."""
    
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False, index=True)  # ✅ CRITICAL
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    # ... other fields
    
    # Relationship
    lab = db.relationship('Lab', backref='patients')
    
    @classmethod
    def get_for_lab(cls, lab_id):
        """Get patients for specific lab only."""
        return cls.query.filter_by(lab_id=lab_id).all()
```

### 4. Example: Protected Endpoint with Data Isolation

```python
@patients_bp.route('', methods=['GET'])
@jwt_required()
@require_lab_access
def list_patients():
    """List patients for current lab only."""
    from app.utils.tenant_context import get_current_lab
    
    lab_id = get_current_lab()
    
    # Only query patients for THIS lab
    patients = Patient.query.filter_by(lab_id=lab_id).all()
    
    return jsonify({
        'patients': patients_schema.dump(patients),
        'lab_id': lab_id
    }), 200
```

### 5. Django Integration Pattern

```python
# In your Django views
def lab_data_view(request, lab_id):
    # Get UMS token from session
    ums_token = request.session.get('ums_token')
    
    # Make request to Flask UMS with lab_id
    response = requests.get(
        f'http://localhost:5000/api/labs/{lab_id}/patients',
        headers={'Authorization': f'Bearer {ums_token}'}
    )
    
    # Flask UMS automatically checks:
    # 1. User is authenticated
    # 2. User has access to this lab
    # 3. Returns ONLY data for this lab
    
    if response.status_code == 403:
        return HttpResponse('Access denied to this lab', status=403)
    
    data = response.json()
    return render(request, 'lab_data.html', {'patients': data['patients']})
```

## Data Isolation Checklist

### ✅ Already Implemented
- [x] Lab entity (tenants)
- [x] LabMembership (user-lab relationships)
- [x] Role-based access (admin, member, viewer)
- [x] Lab admin decorator
- [x] System admin bypass

### ⚠️ MUST Implement for Data Isolation
- [ ] **Add `lab_id` to ALL lab-specific tables**
- [ ] **Always filter queries by lab_id**
- [ ] **Validate lab access in all endpoints**
- [ ] **Use tenant context middleware**
- [ ] **Prevent cross-lab data leakage**

### 🔒 Security Rules

**CRITICAL: For every lab-specific resource:**

1. **Database Level**
   ```sql
   -- Always include lab_id foreign key
   CREATE TABLE patients (
       id INTEGER PRIMARY KEY,
       lab_id INTEGER NOT NULL REFERENCES labs(id),  -- ✅ REQUIRED
       -- ... other fields
   );
   
   -- Always index lab_id
   CREATE INDEX idx_patients_lab_id ON patients(lab_id);
   ```

2. **Query Level**
   ```python
   # ❌ WRONG - No lab filtering
   patients = Patient.query.all()
   
   # ✅ CORRECT - Always filter by lab
   patients = Patient.query.filter_by(lab_id=current_lab_id).all()
   ```

3. **API Level**
   ```python
   # ❌ WRONG - No access check
   @app.route('/patients/<int:patient_id>')
   def get_patient(patient_id):
       patient = Patient.query.get(patient_id)
       return jsonify(patient)
   
   # ✅ CORRECT - Verify lab access
   @app.route('/labs/<int:lab_id>/patients/<int:patient_id>')
   @require_lab_access
   def get_patient(lab_id, patient_id):
       patient = Patient.query.filter_by(
           id=patient_id,
           lab_id=lab_id  # ✅ Ensure patient belongs to this lab
       ).first_or_404()
       return jsonify(patient)
   ```

## URL Structure for Multi-Tenancy

### Recommended Pattern
```
/api/labs/{lab_id}/patients          - List patients in lab
/api/labs/{lab_id}/patients/{id}     - Get specific patient
/api/labs/{lab_id}/tests              - List tests in lab
/api/labs/{lab_id}/reports            - List reports in lab
```

### Benefits
1. Lab context is explicit in URL
2. Easy to validate access
3. Clear data ownership
4. RESTful design

## Example: Complete Implementation

### 1. Create Model
```python
# app/models/patient.py
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), nullable=False, index=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    
    lab = db.relationship('Lab', backref='patients')
```

### 2. Create Route
```python
# app/routes/patients.py
from app.utils.decorators import require_lab_access
from app.utils.tenant_context import get_current_lab

@patients_bp.route('/<int:lab_id>/patients', methods=['GET'])
@jwt_required()
@require_lab_access
def list_patients(lab_id):
    # lab_id already validated by decorator
    patients = Patient.query.filter_by(lab_id=lab_id).all()
    return jsonify({'patients': patients_schema.dump(patients)})

@patients_bp.route('/<int:lab_id>/patients', methods=['POST'])
@jwt_required()
@require_lab_access
def create_patient(lab_id):
    data = request.get_json()
    
    # CRITICAL: Force lab_id from URL, not from request body
    patient = Patient(
        lab_id=lab_id,  # ✅ Use URL parameter, not user input
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    
    db.session.add(patient)
    db.session.commit()
    
    return jsonify({'patient': patient_schema.dump(patient)}), 201
```

## Testing Data Isolation

```python
# tests/test_data_isolation.py
def test_user_cannot_access_other_lab_data(client):
    # User 1 in Lab A
    user1 = create_user('user1')
    lab_a = create_lab('Lab A')
    add_user_to_lab(user1, lab_a, role='member')
    
    # User 2 in Lab B
    user2 = create_user('user2')
    lab_b = create_lab('Lab B')
    add_user_to_lab(user2, lab_b, role='member')
    
    # Create patient in Lab A
    patient_a = create_patient(lab_a, 'Patient A')
    
    # Login as User 2 (Lab B)
    token = login_user(client, 'user2')
    
    # Try to access Lab A's patient
    response = client.get(
        f'/api/labs/{lab_a.id}/patients/{patient_a.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Should be forbidden
    assert response.status_code == 403
    assert 'Access to this lab is forbidden' in response.json['error']
```

## Migration Guide

### Step 1: Add lab_id to Existing Tables
```python
# migration script
def upgrade():
    op.add_column('patients', sa.Column('lab_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_patients_lab_id', 'patients', 'labs', ['lab_id'], ['id'])
    op.create_index('idx_patients_lab_id', 'patients', ['lab_id'])
    
    # Make lab_id NOT NULL after data migration
    # op.alter_column('patients', 'lab_id', nullable=False)
```

### Step 2: Migrate Existing Data
```python
# Assign existing data to a default lab or prompt for lab assignment
default_lab = Lab.query.first()
Patient.query.update({Patient.lab_id: default_lab.id})
db.session.commit()
```

### Step 3: Update Queries
```python
# Before
patients = Patient.query.all()

# After
from app.utils.tenant_context import get_current_lab
lab_id = get_current_lab()
patients = Patient.query.filter_by(lab_id=lab_id).all()
```

## Summary

Your UMS **has the foundation** for multi-tenancy:
- ✅ Lab entities
- ✅ User-lab memberships
- ✅ Role-based access

But **DOES NOT have data isolation** yet. You need to:
1. Add `lab_id` to all lab-specific models
2. Always filter queries by lab
3. Use `@require_lab_access` decorator
4. Validate lab access in every endpoint

**Bottom line:** You have multi-tenancy **structure** but not **enforcement**. Add the data isolation layer before deploying!
