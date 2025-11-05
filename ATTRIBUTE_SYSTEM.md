# Attribute-Based Authorization System

## Overview

The Flask UMS now includes a comprehensive **attribute-based authorization system** that enables fine-grained permission control beyond simple role-based access. This system allows lab owners to grant specific permissions to users, supporting temporary access, permission delegation, and integration with external services.

## Key Features

### 1. Fine-Grained Permissions

Instead of broad roles (admin, member, viewer), the system supports specific permissions like:
- `lab.patient.read` - View patient data
- `lab.patient.write` - Create/edit patient data
- `lab.patient.export` - Export patient data
- `lab.reports.create` - Create reports
- `lab.samples.track` - Track sample status

### 2. Three-Tier Permission Model

**Tier 1: Role-Based Attributes**
- Default permissions for admin, member, and viewer roles
- Applied globally across all labs or specific to individual labs
- Example: All "member" roles get `lab.patient.read` and `lab.patient.write`

**Tier 2: User-Specific Attributes**
- Individual permission grants to specific users
- Can override or extend role-based permissions
- Support for expiration dates (temporary access)
- Example: Grant `lab.patient.export` to a researcher for 30 days

**Tier 3: System Admin Attributes**
- System administrators automatically receive all permissions
- Supports both lab-specific and system-wide operations

### 3. Authorization Forwarding

Other services (Django apps, microservices) can validate user permissions by calling UMS endpoints:

**Check Authorization:**
```http
POST /api/auth/authorize
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "user_id": 123,
  "lab_id": 5,
  "required_attributes": ["lab.patient.read", "lab.reports.view"]
}
```

**Response:**
```json
{
  "user_id": 123,
  "lab_id": 5,
  "lab_name": "Cancer Research Lab",
  "has_access": true,
  "granted_attributes": ["lab.patient.read", "lab.reports.view"],
  "missing_attributes": [],
  "all_user_attributes": ["lab.patient.read", "lab.patient.write", "lab.reports.view", ...],
  "is_system_admin": false
}
```

## Database Schema

### Tables

**attributes**
- id (PK)
- name - Attribute identifier (e.g., "lab.patient.read")
- display_name - Human-readable name
- description - Detailed description
- category - "lab" or "system"
- is_active - Enable/disable attribute

**role_attributes**
- id (PK)
- role_name - Role identifier ("admin", "member", "viewer")
- attribute_id (FK to attributes)
- lab_id (FK to labs, nullable) - Specific lab or global
- granted_by_user_id (FK to users)
- granted_at - Timestamp

**user_lab_attributes**
- id (PK)
- user_id (FK to users)
- lab_id (FK to labs)
- attribute_id (FK to attributes)
- granted_by_user_id (FK to users)
- granted_at - Timestamp
- expires_at - Optional expiration date
- is_active - Enable/disable grant

### Relationships

```
User ──< LabMembership >── Lab
  │
  └──< UserLabAttribute >── Attribute
                             ↑
                             │
         RoleAttribute ──────┘
```

## API Endpoints

### Attribute Management

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/attributes` | GET | List all attributes | Lab Member |
| `/api/attributes` | POST | Create new attribute | Lab Admin |
| `/api/attributes/:id` | GET | Get attribute details | Lab Member |
| `/api/attributes/:id` | PUT | Update attribute | System Admin |
| `/api/attributes/:id` | DELETE | Delete attribute | System Admin |

### Role-Attribute Management

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/attributes/roles` | POST | Assign attribute to role | Lab Admin |
| `/api/attributes/roles/:id` | DELETE | Remove role-attribute mapping | Lab Admin |
| `/api/attributes/roles/lab/:lab_id` | GET | Get role attributes for lab | Lab Admin |

### User-Attribute Management

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/attributes/users` | POST | Grant attribute to user | Lab Admin |
| `/api/attributes/users/:id` | DELETE | Revoke user attribute | Lab Admin |
| `/api/attributes/users/lab/:lab_id/user/:user_id` | GET | Get user's granted attributes | Lab Admin |

### Authorization

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/api/auth/authorize` | POST | Check user authorization | JWT Token |
| `/api/auth/user-attributes` | POST | Get all user attributes for lab | JWT Token |

## Usage Examples

### 1. Create a New Attribute

```python
POST /api/attributes
{
  "name": "lab.genomics.sequence",
  "display_name": "Genomic Sequencing",
  "description": "Permission to run genomic sequencing workflows",
  "category": "lab"
}
```

### 2. Assign Attribute to Role

```python
POST /api/attributes/roles
{
  "role_name": "member",
  "attribute_id": 42,
  "lab_id": 5  # Optional: specific to this lab
}
```

### 3. Grant Temporary Access to User

```python
POST /api/attributes/users
{
  "user_id": 123,
  "lab_id": 5,
  "attribute_id": 15,  # lab.patient.export
  "expires_in_days": 30
}
```

### 4. Check User Authorization (Service Integration)

```python
import requests

def check_user_permission(token, user_id, lab_id, required_permissions):
    response = requests.post(
        'https://ums.example.com/api/auth/authorize',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'user_id': user_id,
            'lab_id': lab_id,
            'required_attributes': required_permissions
        }
    )
    data = response.json()
    return data['has_access']

# Usage in Django view
if check_user_permission(token, user_id, lab_id, ['lab.patient.read']):
    # Allow access to patient data
    pass
```

### 5. Using Decorators in Flask Routes

```python
from app.utils.attribute_decorators import require_attributes

@app.route('/labs/<int:lab_id>/patients/export')
@jwt_required()
@require_attributes(['lab.patient.export'], lab_id_param='lab_id')
def export_patients(lab_id):
    # User is guaranteed to have lab.patient.export permission
    patients = Patient.query.filter_by(lab_id=lab_id).all()
    return export_to_csv(patients)

@app.route('/labs/<int:lab_id>/reports/create')
@jwt_required()
@require_any_attributes(
    ['lab.reports.create', 'lab.admin.manage'],
    lab_id_param='lab_id'
)
def create_report(lab_id):
    # User has either lab.reports.create OR lab.admin.manage
    pass
```

## Pre-Configured Attributes

The system comes with 39 pre-configured attributes across different categories:

### Lab Management (5 attributes)
- lab.admin.manage
- lab.settings.edit
- lab.users.invite
- lab.users.remove
- lab.roles.assign

### Patient Data (4 attributes)
- lab.patient.read
- lab.patient.write
- lab.patient.delete
- lab.patient.export

### Reports & Analytics (4 attributes)
- lab.reports.view
- lab.reports.create
- lab.reports.export
- lab.reports.schedule

### Sample Management (4 attributes)
- lab.samples.read
- lab.samples.write
- lab.samples.track
- lab.samples.dispose

### Equipment (3 attributes)
- lab.equipment.view
- lab.equipment.reserve
- lab.equipment.maintain

### Data Analysis (3 attributes)
- lab.analysis.run
- lab.analysis.results
- lab.analysis.configure

### Quality Control (3 attributes)
- lab.qc.view
- lab.qc.perform
- lab.qc.approve

### Billing & Finance (3 attributes)
- lab.billing.view
- lab.billing.manage
- lab.costs.track

### Compliance & Audit (3 attributes)
- lab.audit.view
- lab.audit.export
- lab.compliance.manage

### Basic Access (2 attributes)
- lab.member.basic
- lab.viewer.read

### System Attributes (6 attributes)
- system.admin.full
- system.users.manage
- system.labs.manage
- system.billing.global
- system.audit.global
- system.maintenance.perform

## Default Role Mappings

### Admin Role (33 attributes)
- All lab management permissions
- Full patient data access (read, write, delete, export)
- Complete reports access
- Full sample management
- Equipment access and maintenance
- Analysis configuration
- QC approval
- Billing and compliance management

### Member Role (14 attributes)
- Patient data (read, write)
- Reports (view, create)
- Sample management (read, write, track)
- Equipment (view, reserve)
- Analysis execution
- QC operations

### Viewer Role (7 attributes)
- Patient data (read only)
- Reports (view only)
- Sample information (read only)
- Equipment status (view only)
- Analysis results (view only)
- QC data (view only)

## Use Cases

### 1. Temporary Research Collaboration

**Scenario:** External researcher needs read access to patient data for 30 days.

**Solution:**
```python
# Grant temporary read access
POST /api/attributes/users
{
  "user_id": 456,
  "lab_id": 5,
  "attribute_id": 6,  # lab.patient.read
  "expires_in_days": 30
}

# Access automatically revoked after 30 days
```

### 2. Quality Control Specialist

**Scenario:** A user should only approve QC results without full admin access.

**Solution:**
```python
# Grant specific QC approval permission
POST /api/attributes/users
{
  "user_id": 789,
  "lab_id": 5,
  "attribute_id": 27  # lab.qc.approve
}

# User can now approve QC without admin privileges
```

### 3. Limited Export Access

**Scenario:** Grant export permission to specific member who normally can't export.

**Solution:**
```python
# Member role doesn't include export by default
# Grant export permission to specific user
POST /api/attributes/users
{
  "user_id": 321,
  "lab_id": 5,
  "attribute_id": 9  # lab.patient.export
}
```

### 4. Service Integration

**Scenario:** Django service needs to verify user can access patient data.

**Solution:**
```python
# Django view
from django.http import JsonResponse
import requests

def patient_list(request, lab_id):
    # Get JWT token from request
    token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
    
    # Check authorization with UMS
    auth_response = requests.post(
        'https://ums.example.com/api/auth/authorize',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'user_id': request.user.id,
            'lab_id': lab_id,
            'required_attributes': ['lab.patient.read']
        }
    )
    
    auth_data = auth_response.json()
    
    if not auth_data.get('has_access'):
        return JsonResponse({
            'error': 'Insufficient permissions',
            'missing': auth_data.get('missing_attributes')
        }, status=403)
    
    # User has permission - proceed with query
    patients = Patient.objects.filter(lab_id=lab_id)
    return JsonResponse({'patients': list(patients.values())})
```

## Migration Guide

### Existing Installations

For systems already using role-based access, the attribute system is backward compatible:

1. **Database Migration:**
   ```bash
   # Backup your database first
   python init_db_with_attributes.py
   ```

2. **Existing users maintain their role-based permissions** through the role-attribute mappings.

3. **Gradually add attributes** as needed without disrupting existing access.

### New Installations

Use the enhanced initialization script:

```bash
python init_db_with_attributes.py
```

This creates:
- 39 pre-configured attributes
- Role-attribute mappings for admin/member/viewer
- Sample users and labs
- Example user-specific attribute grant

## Security Considerations

1. **Attribute Validation:** Attribute names follow strict format: `category.resource.action`

2. **Expiration Enforcement:** Expired user attributes are automatically excluded from authorization checks

3. **Audit Logging:** All attribute grants and revocations are logged with:
   - Who granted/revoked
   - When it occurred
   - Which attribute
   - To/from which user

4. **Permission Hierarchy:** System admins automatically get all permissions

5. **Lab Isolation:** Attributes are scoped to specific labs, maintaining multi-tenant isolation

## Performance

The attribute system is optimized for production use:

- **Caching:** User attributes can be cached with JWT claims (future enhancement)
- **Database Indexes:** Proper indexing on user_id, lab_id, and attribute_id
- **Query Optimization:** Single query to fetch all user attributes for a lab
- **Graceful Degradation:** Authorization checks return empty list on error

## Testing

Comprehensive test suite included in `tests/test_attributes.py`:

```bash
# Run attribute system tests
python -m pytest tests/test_attributes.py -v

# Test coverage
python -m pytest tests/test_attributes.py --cov=app.routes.attributes --cov=app.models.attribute
```

Tests cover:
- Attribute creation and management
- Role-attribute assignment
- User-specific grants
- Authorization checks
- Expired attribute handling
- System admin permissions
- Permission revocation

## Future Enhancements

1. **Attribute Groups:** Bundle related attributes for easier management
2. **Attribute Inheritance:** Parent-child attribute relationships
3. **Conditional Attributes:** Time-based or IP-based attribute activation
4. **Attribute Analytics:** Track attribute usage and access patterns
5. **Bulk Operations:** Assign/revoke attributes for multiple users
6. **Attribute Templates:** Pre-defined attribute sets for common scenarios

## Support

For questions or issues related to the attribute system:

1. Check the [FEATURES.md](FEATURES.md#-attribute-based-authorization) documentation
2. Review [README.md](README.md) for integration examples
3. See test files for implementation patterns
