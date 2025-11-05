"""Initialize the database with sample data and attribute system."""
from app import create_app, db
from app.models import User, Lab, LabMembership, Attribute, RoleAttribute, UserLabAttribute
from datetime import datetime, timedelta


def init_database():
    """Initialize database with sample data."""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create sample attributes
        create_sample_attributes()
        
        # Create sample users
        admin_user = create_sample_user(
            username='admin',
            email='admin@example.com',
            first_name='System',
            last_name='Administrator',
            is_admin=True
        )
        
        lab_admin = create_sample_user(
            username='labadmin',
            email='labadmin@example.com',
            first_name='Lab',
            last_name='Administrator'
        )
        
        researcher = create_sample_user(
            username='researcher',
            email='researcher@example.com',
            first_name='Research',
            last_name='Scientist'
        )
        
        viewer = create_sample_user(
            username='viewer',
            email='viewer@example.com',
            first_name='Data',
            last_name='Viewer'
        )
        
        # Create sample labs
        cancer_lab = create_sample_lab(
            name='Cancer Research Lab',
            code='CRL001',
            description='Advanced cancer research and treatment development'
        )
        
        genetics_lab = create_sample_lab(
            name='Genetics Lab',
            code='GEN001',
            description='Genetic analysis and genomic research'
        )
        
        # Create lab memberships
        create_lab_membership(lab_admin.id, cancer_lab.id, 'admin')
        create_lab_membership(researcher.id, cancer_lab.id, 'member')
        create_lab_membership(viewer.id, cancer_lab.id, 'viewer')
        
        create_lab_membership(lab_admin.id, genetics_lab.id, 'member')
        create_lab_membership(researcher.id, genetics_lab.id, 'admin')
        
        # Create role-attribute mappings
        create_role_attribute_mappings()
        
        # Create sample user-specific attributes
        create_sample_user_attributes(researcher.id, cancer_lab.id)
        
        db.session.commit()
        print("Database initialized successfully!")
        print_sample_data_summary()


def create_sample_attributes():
    """Create sample attributes for the system."""
    
    # Lab management attributes
    lab_attributes = [
        ('lab.admin.manage', 'Lab Administration', 'Full lab administration including user management'),
        ('lab.settings.edit', 'Lab Settings', 'Edit lab configuration and settings'),
        ('lab.users.invite', 'Invite Users', 'Invite new users to the lab'),
        ('lab.users.remove', 'Remove Users', 'Remove users from the lab'),
        ('lab.roles.assign', 'Assign Roles', 'Assign roles to lab members'),
        
        # Patient data attributes
        ('lab.patient.read', 'Read Patient Data', 'View patient information and records'),
        ('lab.patient.write', 'Write Patient Data', 'Create and edit patient records'),
        ('lab.patient.delete', 'Delete Patient Data', 'Delete patient records'),
        ('lab.patient.export', 'Export Patient Data', 'Export patient data for analysis'),
        
        # Reports and analytics
        ('lab.reports.view', 'View Reports', 'View lab reports and analytics'),
        ('lab.reports.create', 'Create Reports', 'Create new reports and analytics'),
        ('lab.reports.export', 'Export Reports', 'Export reports to external formats'),
        ('lab.reports.schedule', 'Schedule Reports', 'Set up automated report generation'),
        
        # Sample and specimen management
        ('lab.samples.read', 'Read Sample Data', 'View sample and specimen information'),
        ('lab.samples.write', 'Write Sample Data', 'Create and edit sample records'),
        ('lab.samples.track', 'Track Samples', 'Track sample location and status'),
        ('lab.samples.dispose', 'Dispose Samples', 'Mark samples for disposal'),
        
        # Equipment and resources
        ('lab.equipment.view', 'View Equipment', 'View equipment status and information'),
        ('lab.equipment.reserve', 'Reserve Equipment', 'Reserve equipment for use'),
        ('lab.equipment.maintain', 'Maintain Equipment', 'Perform equipment maintenance'),
        
        # Data analysis
        ('lab.analysis.run', 'Run Analysis', 'Execute data analysis workflows'),
        ('lab.analysis.results', 'View Analysis Results', 'View analysis results and outputs'),
        ('lab.analysis.configure', 'Configure Analysis', 'Set up analysis parameters and workflows'),
        
        # Quality control
        ('lab.qc.view', 'View QC Data', 'View quality control information'),
        ('lab.qc.perform', 'Perform QC', 'Conduct quality control procedures'),
        ('lab.qc.approve', 'Approve QC', 'Approve quality control results'),
        
        # Billing and finance
        ('lab.billing.view', 'View Billing', 'View billing information and invoices'),
        ('lab.billing.manage', 'Manage Billing', 'Create and manage billing records'),
        ('lab.costs.track', 'Track Costs', 'Monitor lab costs and expenses'),
        
        # Compliance and audit
        ('lab.audit.view', 'View Audit Logs', 'View system audit logs'),
        ('lab.audit.export', 'Export Audit Data', 'Export audit logs for compliance'),
        ('lab.compliance.manage', 'Manage Compliance', 'Handle compliance requirements'),
        
        # Basic member permissions
        ('lab.member.basic', 'Basic Lab Access', 'Basic lab member access'),
        ('lab.viewer.read', 'Read-Only Access', 'Read-only access to lab data'),
    ]
    
    # System-wide attributes
    system_attributes = [
        ('system.admin.full', 'System Administration', 'Full system administration access'),
        ('system.users.manage', 'Manage All Users', 'Manage users across all labs'),
        ('system.labs.manage', 'Manage All Labs', 'Create and manage labs system-wide'),
        ('system.billing.global', 'Global Billing', 'Access to all billing information'),
        ('system.audit.global', 'Global Audit Access', 'Access to all system audit logs'),
        ('system.maintenance.perform', 'System Maintenance', 'Perform system maintenance tasks'),
    ]
    
    # Create lab attributes
    for name, display_name, description in lab_attributes:
        attr = Attribute(
            name=name,
            display_name=display_name,
            description=description,
            category='lab',
            is_active=True
        )
        db.session.add(attr)
    
    # Create system attributes
    for name, display_name, description in system_attributes:
        attr = Attribute(
            name=name,
            display_name=display_name,
            description=description,
            category='system',
            is_active=True
        )
        db.session.add(attr)
    
    db.session.flush()  # Flush to get IDs


def create_role_attribute_mappings():
    """Create default role-attribute mappings."""
    
    # Admin role attributes (lab-specific)
    admin_attributes = [
        'lab.admin.manage',
        'lab.settings.edit',
        'lab.users.invite',
        'lab.users.remove',
        'lab.roles.assign',
        'lab.patient.read',
        'lab.patient.write',
        'lab.patient.delete',
        'lab.patient.export',
        'lab.reports.view',
        'lab.reports.create',
        'lab.reports.export',
        'lab.reports.schedule',
        'lab.samples.read',
        'lab.samples.write',
        'lab.samples.track',
        'lab.samples.dispose',
        'lab.equipment.view',
        'lab.equipment.reserve',
        'lab.equipment.maintain',
        'lab.analysis.run',
        'lab.analysis.results',
        'lab.analysis.configure',
        'lab.qc.view',
        'lab.qc.perform',
        'lab.qc.approve',
        'lab.billing.view',
        'lab.billing.manage',
        'lab.costs.track',
        'lab.audit.view',
        'lab.audit.export',
        'lab.compliance.manage',
        'lab.member.basic',
    ]
    
    # Member role attributes
    member_attributes = [
        'lab.patient.read',
        'lab.patient.write',
        'lab.reports.view',
        'lab.reports.create',
        'lab.samples.read',
        'lab.samples.write',
        'lab.samples.track',
        'lab.equipment.view',
        'lab.equipment.reserve',
        'lab.analysis.run',
        'lab.analysis.results',
        'lab.qc.view',
        'lab.qc.perform',
        'lab.member.basic',
    ]
    
    # Viewer role attributes
    viewer_attributes = [
        'lab.patient.read',
        'lab.reports.view',
        'lab.samples.read',
        'lab.equipment.view',
        'lab.analysis.results',
        'lab.qc.view',
        'lab.viewer.read',
    ]
    
    # Create role-attribute mappings for admin
    for attr_name in admin_attributes:
        attr = Attribute.query.filter_by(name=attr_name).first()
        if attr:
            role_attr = RoleAttribute(
                role_name='admin',
                attribute_id=attr.id,
                lab_id=None,  # Apply to all labs
                granted_by_user_id=1,  # System user
                granted_at=datetime.utcnow()
            )
            db.session.add(role_attr)
    
    # Create role-attribute mappings for member
    for attr_name in member_attributes:
        attr = Attribute.query.filter_by(name=attr_name).first()
        if attr:
            role_attr = RoleAttribute(
                role_name='member',
                attribute_id=attr.id,
                lab_id=None,  # Apply to all labs
                granted_by_user_id=1,  # System user
                granted_at=datetime.utcnow()
            )
            db.session.add(role_attr)
    
    # Create role-attribute mappings for viewer
    for attr_name in viewer_attributes:
        attr = Attribute.query.filter_by(name=attr_name).first()
        if attr:
            role_attr = RoleAttribute(
                role_name='viewer',
                attribute_id=attr.id,
                lab_id=None,  # Apply to all labs
                granted_by_user_id=1,  # System user
                granted_at=datetime.utcnow()
            )
            db.session.add(role_attr)


def create_sample_user_attributes(user_id, lab_id):
    """Create sample user-specific attributes."""
    
    # Give the researcher special export permissions for this specific lab
    export_attr = Attribute.query.filter_by(name='lab.patient.export').first()
    if export_attr:
        user_attr = UserLabAttribute(
            user_id=user_id,
            lab_id=lab_id,
            attribute_id=export_attr.id,
            granted_by_user_id=1,  # System user
            granted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),  # 1 year
            is_active=True
        )
        db.session.add(user_attr)


def create_sample_user(username, email, first_name, last_name, is_admin=False):
    """Create a sample user."""
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_admin=is_admin,
        is_active=True
    )
    user.set_password('Password123!')  # HIPAA-compliant password
    
    db.session.add(user)
    db.session.flush()  # Get the ID
    return user


def create_sample_lab(name, code, description):
    """Create a sample lab."""
    lab = Lab(
        name=name,
        code=code,
        description=description,
        is_active=True
    )
    
    db.session.add(lab)
    db.session.flush()  # Get the ID
    return lab


def create_lab_membership(user_id, lab_id, role):
    """Create a lab membership."""
    membership = LabMembership(
        user_id=user_id,
        lab_id=lab_id,
        role=role,
        joined_at=datetime.utcnow(),
        is_active=True
    )
    
    db.session.add(membership)
    return membership


def print_sample_data_summary():
    """Print a summary of the created sample data."""
    print("\n" + "="*60)
    print("SAMPLE DATA SUMMARY")
    print("="*60)
    
    # Users
    users = User.query.all()
    print(f"\nUsers created: {len(users)}")
    for user in users:
        print(f"  - {user.username} ({user.email}) - Admin: {user.is_admin}")
    
    # Labs
    labs = Lab.query.all()
    print(f"\nLabs created: {len(labs)}")
    for lab in labs:
        print(f"  - {lab.name} ({lab.code})")
    
    # Attributes
    attributes = Attribute.query.all()
    print(f"\nAttributes created: {len(attributes)}")
    lab_attrs = [a for a in attributes if a.category == 'lab']
    system_attrs = [a for a in attributes if a.category == 'system']
    print(f"  - Lab attributes: {len(lab_attrs)}")
    print(f"  - System attributes: {len(system_attrs)}")
    
    # Role mappings
    role_attrs = RoleAttribute.query.all()
    print(f"\nRole-attribute mappings: {len(role_attrs)}")
    admin_mappings = len([ra for ra in role_attrs if ra.role_name == 'admin'])
    member_mappings = len([ra for ra in role_attrs if ra.role_name == 'member'])
    viewer_mappings = len([ra for ra in role_attrs if ra.role_name == 'viewer'])
    print(f"  - Admin role: {admin_mappings} attributes")
    print(f"  - Member role: {member_mappings} attributes")
    print(f"  - Viewer role: {viewer_mappings} attributes")
    
    # User-specific attributes
    user_attrs = UserLabAttribute.query.all()
    print(f"\nUser-specific attributes: {len(user_attrs)}")
    
    print("\n" + "="*60)
    print("LOGIN CREDENTIALS (All passwords: Password123!)")
    print("="*60)
    print("System Admin: admin / admin@example.com")
    print("Lab Admin: labadmin / labadmin@example.com")
    print("Researcher: researcher / researcher@example.com")
    print("Viewer: viewer / viewer@example.com")
    print("="*60)


def create_admin_user():
    """Create an admin user interactively."""
    app = create_app()
    
    with app.app_context():
        print("\n--- Create Admin User ---")
        username = input("Enter admin username: ")
        email = input("Enter admin email: ")
        password = input("Enter admin password: ")
        first_name = input("Enter first name (optional): ")
        last_name = input("Enter last name (optional): ")
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"✗ Error: Username '{username}' already exists!")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"✗ Error: Email '{email}' already exists!")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None,
            is_admin=True,
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"\n✓ Admin user '{username}' created successfully!")
        print(f"  ID: {admin.id}")
        print(f"  Email: {admin.email}")
        print(f"  Is Admin: {admin.is_admin}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'create-admin':
        create_admin_user()
    else:
        init_database()
        print("\nTo create an admin user only, run:")
        print("  python init_db.py create-admin")