"""Tests for multi-tenant data isolation."""
import pytest
from app import create_app, db
from app.models.user import User
from app.models.lab import Lab, LabMembership


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def create_test_user(username, email, password='testpass123'):
    """Helper to create a test user."""
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def create_test_lab(name, code):
    """Helper to create a test lab."""
    lab = Lab(name=name, code=code)
    db.session.add(lab)
    db.session.commit()
    return lab


def add_user_to_lab(user, lab, role='member'):
    """Helper to add user to a lab."""
    membership = LabMembership(user_id=user.id, lab_id=lab.id, role=role)
    db.session.add(membership)
    db.session.commit()
    return membership


def login_user(client, username, password='testpass123'):
    """Helper to login and get access token."""
    response = client.post('/api/auth/login', json={
        'username': username,
        'password': password
    })
    return response.json.get('access_token')


class TestDataIsolation:
    """Test data isolation between labs."""
    
    def test_user_can_only_see_their_labs(self, client):
        """Test that users only see labs they're members of."""
        # Create two labs
        lab_a = create_test_lab('Lab A', 'LABA')
        lab_b = create_test_lab('Lab B', 'LABB')
        
        # Create user in Lab A only
        user1 = create_test_user('user1', 'user1@test.com')
        add_user_to_lab(user1, lab_a)
        
        # Login as user1
        token = login_user(client, 'user1')
        
        # Get labs list
        response = client.get('/api/labs', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        labs = response.json['labs']
        
        # Should only see Lab A
        assert len(labs) == 1
        assert labs[0]['code'] == 'LABA'
    
    def test_user_cannot_access_other_lab(self, client):
        """Test that users cannot access labs they're not members of."""
        # Create two labs
        lab_a = create_test_lab('Lab A', 'LABA')
        lab_b = create_test_lab('Lab B', 'LABB')
        
        # User1 in Lab A, User2 in Lab B
        user1 = create_test_user('user1', 'user1@test.com')
        add_user_to_lab(user1, lab_a)
        
        user2 = create_test_user('user2', 'user2@test.com')
        add_user_to_lab(user2, lab_b)
        
        # Login as user1
        token = login_user(client, 'user1')
        
        # Try to access Lab B
        response = client.get(f'/api/labs/{lab_b.id}', headers={
            'Authorization': f'Bearer {token}'
        })
        
        # Should be forbidden
        assert response.status_code == 403
        assert 'forbidden' in response.json['error'].lower()
    
    def test_user_cannot_see_other_lab_members(self, client):
        """Test that users cannot see members of other labs."""
        # Create two labs
        lab_a = create_test_lab('Lab A', 'LABA')
        lab_b = create_test_lab('Lab B', 'LABB')
        
        # User1 in Lab A, User2 in Lab B
        user1 = create_test_user('user1', 'user1@test.com')
        add_user_to_lab(user1, lab_a)
        
        user2 = create_test_user('user2', 'user2@test.com')
        add_user_to_lab(user2, lab_b)
        
        # Login as user1
        token = login_user(client, 'user1')
        
        # Try to get Lab B members
        response = client.get(f'/api/labs/{lab_b.id}/members', headers={
            'Authorization': f'Bearer {token}'
        })
        
        # Should be forbidden
        assert response.status_code == 403
    
    def test_admin_can_access_all_labs(self, client):
        """Test that system admins can access all labs."""
        # Create labs
        lab_a = create_test_lab('Lab A', 'LABA')
        lab_b = create_test_lab('Lab B', 'LABB')
        
        # Create admin user (not added to any lab)
        admin = create_test_user('admin', 'admin@test.com')
        admin.is_admin = True
        db.session.commit()
        
        # Login as admin
        token = login_user(client, 'admin')
        
        # Get all labs
        response = client.get('/api/labs', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        labs = response.json['labs']
        
        # Admin should see all labs
        assert len(labs) == 2
    
    def test_user_in_multiple_labs(self, client):
        """Test that users can belong to multiple labs."""
        # Create labs
        lab_a = create_test_lab('Lab A', 'LABA')
        lab_b = create_test_lab('Lab B', 'LABB')
        lab_c = create_test_lab('Lab C', 'LABC')
        
        # User in Lab A and Lab B
        user1 = create_test_user('user1', 'user1@test.com')
        add_user_to_lab(user1, lab_a)
        add_user_to_lab(user1, lab_b)
        
        # Login
        token = login_user(client, 'user1')
        
        # Get labs
        response = client.get('/api/labs', headers={
            'Authorization': f'Bearer {token}'
        })
        
        assert response.status_code == 200
        labs = response.json['labs']
        
        # Should see Lab A and Lab B only
        assert len(labs) == 2
        lab_codes = {lab['code'] for lab in labs}
        assert lab_codes == {'LABA', 'LABB'}
    
    def test_lab_admin_can_add_members(self, client):
        """Test that lab admins can add members to their lab."""
        # Create lab and users
        lab = create_test_lab('Lab A', 'LABA')
        admin_user = create_test_user('admin', 'admin@test.com')
        new_user = create_test_user('newuser', 'new@test.com')
        
        # Make admin_user a lab admin
        add_user_to_lab(admin_user, lab, role='admin')
        
        # Login as lab admin
        token = login_user(client, 'admin')
        
        # Add new member
        response = client.post(f'/api/labs/{lab.id}/members', 
            headers={'Authorization': f'Bearer {token}'},
            json={'user_id': new_user.id, 'role': 'member'}
        )
        
        assert response.status_code == 201
    
    def test_member_cannot_add_members(self, client):
        """Test that regular members cannot add members."""
        # Create lab and users
        lab = create_test_lab('Lab A', 'LABA')
        member = create_test_user('member', 'member@test.com')
        new_user = create_test_user('newuser', 'new@test.com')
        
        # Add as regular member
        add_user_to_lab(member, lab, role='member')
        
        # Login as member
        token = login_user(client, 'member')
        
        # Try to add new member (should fail)
        response = client.post(f'/api/labs/{lab.id}/members',
            headers={'Authorization': f'Bearer {token}'},
            json={'user_id': new_user.id, 'role': 'member'}
        )
        
        assert response.status_code == 403


class TestTenantContext:
    """Test tenant context utilities."""
    
    def test_get_current_user_labs(self, app):
        """Test getting current user's labs."""
        from app.utils.tenant_context import get_current_user_labs
        from flask_jwt_extended import create_access_token
        
        with app.app_context():
            # Create user and labs
            lab_a = create_test_lab('Lab A', 'LABA')
            lab_b = create_test_lab('Lab B', 'LABB')
            user = create_test_user('user1', 'user1@test.com')
            add_user_to_lab(user, lab_a)
            
            # Create token and test
            with app.test_request_context(headers={
                'Authorization': f'Bearer {create_access_token(identity=user.id)}'
            }):
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request()
                
                labs = get_current_user_labs()
                assert len(labs) == 1
                assert lab_a.id in labs
                assert lab_b.id not in labs
    
    def test_verify_lab_access(self, app):
        """Test lab access verification."""
        from app.utils.tenant_context import verify_lab_access
        from flask_jwt_extended import create_access_token
        
        with app.app_context():
            # Create user and labs
            lab_a = create_test_lab('Lab A', 'LABA')
            lab_b = create_test_lab('Lab B', 'LABB')
            user = create_test_user('user1', 'user1@test.com')
            add_user_to_lab(user, lab_a)
            
            # Test access
            with app.test_request_context(headers={
                'Authorization': f'Bearer {create_access_token(identity=user.id)}'
            }):
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request()
                
                # Should have access to Lab A
                assert verify_lab_access(lab_a.id) == True
                
                # Should NOT have access to Lab B
                assert verify_lab_access(lab_b.id) == False
