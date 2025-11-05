"""Tests for attribute-based authorization system."""
import unittest
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Lab, LabMembership, Attribute, RoleAttribute, UserLabAttribute


class TestAttributeSystem(unittest.TestCase):
    """Test cases for attribute-based authorization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """Create test users, labs, and attributes."""
        # Create users
        self.admin_user = User(
            username='admin',
            email='admin@test.com',
            is_admin=True,
            is_active=True
        )
        self.admin_user.set_password('Password123!')
        
        self.lab_admin = User(
            username='labadmin',
            email='labadmin@test.com',
            is_active=True
        )
        self.lab_admin.set_password('Password123!')
        
        self.member = User(
            username='member',
            email='member@test.com',
            is_active=True
        )
        self.member.set_password('Password123!')
        
        self.viewer = User(
            username='viewer',
            email='viewer@test.com',
            is_active=True
        )
        self.viewer.set_password('Password123!')
        
        db.session.add_all([self.admin_user, self.lab_admin, self.member, self.viewer])
        db.session.flush()
        
        # Create lab
        self.lab = Lab(
            name='Test Lab',
            code='TEST001',
            description='Test laboratory',
            is_active=True
        )
        db.session.add(self.lab)
        db.session.flush()
        
        # Create lab memberships
        db.session.add(LabMembership(
            user_id=self.lab_admin.id,
            lab_id=self.lab.id,
            role='admin',
            is_active=True
        ))
        db.session.add(LabMembership(
            user_id=self.member.id,
            lab_id=self.lab.id,
            role='member',
            is_active=True
        ))
        db.session.add(LabMembership(
            user_id=self.viewer.id,
            lab_id=self.lab.id,
            role='viewer',
            is_active=True
        ))
        
        # Create attributes
        self.attr_admin = Attribute(
            name='lab.admin.manage',
            display_name='Lab Administration',
            description='Full lab admin access',
            category='lab',
            is_active=True
        )
        self.attr_read = Attribute(
            name='lab.patient.read',
            display_name='Read Patient Data',
            description='Read patient records',
            category='lab',
            is_active=True
        )
        self.attr_write = Attribute(
            name='lab.patient.write',
            display_name='Write Patient Data',
            description='Create/edit patient records',
            category='lab',
            is_active=True
        )
        self.attr_delete = Attribute(
            name='lab.patient.delete',
            display_name='Delete Patient Data',
            description='Delete patient records',
            category='lab',
            is_active=True
        )
        
        db.session.add_all([self.attr_admin, self.attr_read, self.attr_write, self.attr_delete])
        db.session.flush()
        
        # Create role-attribute mappings
        # Admin role gets all attributes
        for attr in [self.attr_admin, self.attr_read, self.attr_write, self.attr_delete]:
            db.session.add(RoleAttribute(
                role_name='admin',
                attribute_id=attr.id,
                granted_by_user_id=self.admin_user.id,
                granted_at=datetime.utcnow()
            ))
        
        # Member role gets read and write
        for attr in [self.attr_read, self.attr_write]:
            db.session.add(RoleAttribute(
                role_name='member',
                attribute_id=attr.id,
                granted_by_user_id=self.admin_user.id,
                granted_at=datetime.utcnow()
            ))
        
        # Viewer role gets only read
        db.session.add(RoleAttribute(
            role_name='viewer',
            attribute_id=self.attr_read.id,
            granted_by_user_id=self.admin_user.id,
            granted_at=datetime.utcnow()
        ))
        
        db.session.commit()
    
    def _login(self, username, password):
        """Helper to login and get JWT token."""
        response = self.client.post('/api/auth/login', json={
            'username': username,
            'password': password
        })
        data = json.loads(response.data)
        return data.get('access_token')
    
    def test_attribute_creation(self):
        """Test creating attributes via API."""
        with self.app.app_context():
            token = self._login('labadmin', 'Password123!')
            
            # Create new attribute
            response = self.client.post(
                '/api/attributes',
                json={
                    'name': 'lab.reports.export',
                    'display_name': 'Export Reports',
                    'description': 'Export report data',
                    'category': 'lab'
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertEqual(data['attribute']['name'], 'lab.reports.export')
    
    def test_list_attributes(self):
        """Test listing all attributes."""
        with self.app.app_context():
            token = self._login('labadmin', 'Password123!')
            
            response = self.client.get(
                '/api/attributes',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertGreaterEqual(len(data['attributes']), 4)
    
    def test_role_attribute_assignment(self):
        """Test assigning attributes to roles."""
        with self.app.app_context():
            token = self._login('labadmin', 'Password123!')
            
            # Create new attribute
            new_attr_response = self.client.post(
                '/api/attributes',
                json={
                    'name': 'lab.samples.track',
                    'display_name': 'Track Samples',
                    'description': 'Track sample status',
                    'category': 'lab'
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            new_attr = json.loads(new_attr_response.data)['attribute']
            
            # Assign to member role
            response = self.client.post(
                f'/api/attributes/roles',
                json={
                    'role_name': 'member',
                    'attribute_id': new_attr['id'],
                    'lab_id': self.lab.id
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 201)
    
    def test_user_specific_attribute_grant(self):
        """Test granting specific attributes to a user."""
        with self.app.app_context():
            token = self._login('labadmin', 'Password123!')
            
            # Grant delete permission to member (who normally only has read/write)
            response = self.client.post(
                f'/api/attributes/users',
                json={
                    'user_id': self.member.id,
                    'lab_id': self.lab.id,
                    'attribute_id': self.attr_delete.id,
                    'expires_in_days': 30
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertIsNotNone(data['user_attribute']['expires_at'])
    
    def test_authorization_check(self):
        """Test the authorization endpoint."""
        with self.app.app_context():
            token = self._login('member', 'Password123!')
            
            # Check if member has read and write permissions
            response = self.client.post(
                '/api/auth/authorize',
                json={
                    'user_id': self.member.id,
                    'lab_id': self.lab.id,
                    'required_attributes': ['lab.patient.read', 'lab.patient.write']
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['has_access'])
            self.assertEqual(len(data['granted_attributes']), 2)
    
    def test_authorization_check_insufficient_permissions(self):
        """Test authorization check when user lacks permissions."""
        with self.app.app_context():
            token = self._login('viewer', 'Password123!')
            
            # Viewer should not have write permission
            response = self.client.post(
                '/api/auth/authorize',
                json={
                    'user_id': self.viewer.id,
                    'lab_id': self.lab.id,
                    'required_attributes': ['lab.patient.write']
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertFalse(data['has_access'])
            self.assertIn('lab.patient.write', data['missing_attributes'])
    
    def test_get_user_attributes(self):
        """Test retrieving all user attributes for a lab."""
        with self.app.app_context():
            token = self._login('labadmin', 'Password123!')
            
            response = self.client.post(
                '/api/auth/user-attributes',
                json={
                    'user_id': self.lab_admin.id,
                    'lab_id': self.lab.id
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('lab.admin.manage', data['attributes'])
            self.assertIn('lab.patient.read', data['attributes'])
    
    def test_expired_user_attribute(self):
        """Test that expired user attributes are not returned."""
        with self.app.app_context():
            # Grant attribute with past expiration
            expired_grant = UserLabAttribute(
                user_id=self.member.id,
                lab_id=self.lab.id,
                attribute_id=self.attr_delete.id,
                granted_by_user_id=self.lab_admin.id,
                granted_at=datetime.utcnow() - timedelta(days=2),
                expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
                is_active=True
            )
            db.session.add(expired_grant)
            db.session.commit()
            
            token = self._login('member', 'Password123!')
            
            response = self.client.post(
                '/api/auth/user-attributes',
                json={
                    'user_id': self.member.id,
                    'lab_id': self.lab.id
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            data = json.loads(response.data)
            # Should not include expired delete permission
            self.assertNotIn('lab.patient.delete', data['attributes'])
    
    def test_system_admin_gets_all_attributes(self):
        """Test that system admins get all lab attributes."""
        with self.app.app_context():
            token = self._login('admin', 'Password123!')
            
            response = self.client.post(
                '/api/auth/user-attributes',
                json={
                    'user_id': self.admin_user.id,
                    'lab_id': self.lab.id
                },
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            # System admin should have all lab attributes
            self.assertGreaterEqual(len(data['attributes']), 4)
    
    def test_revoke_user_attribute(self):
        """Test revoking a user-specific attribute grant."""
        with self.app.app_context():
            # First grant the attribute
            grant = UserLabAttribute(
                user_id=self.member.id,
                lab_id=self.lab.id,
                attribute_id=self.attr_delete.id,
                granted_by_user_id=self.lab_admin.id,
                granted_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(grant)
            db.session.commit()
            
            token = self._login('labadmin', 'Password123!')
            
            # Revoke it
            response = self.client.delete(
                f'/api/attributes/users/{grant.id}',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify it's revoked
            db.session.refresh(grant)
            self.assertFalse(grant.is_active)


if __name__ == '__main__':
    unittest.main()