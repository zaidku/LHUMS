# Flask User Management Service (UMS) v1.0

A production-ready, HIPAA-compliant User Management Service built with Flask to provide centralized authentication and multi-tenant user management for Django webapp portals.

[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/zaidku/LHUMS)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Key Features

### Authentication & Security
- ✅ **JWT-based Authentication** - Secure access & refresh tokens
- ✅ **Password Management** - Reset, change, expiration (90-day HIPAA rotation)
- ✅ **Account Security** - Auto-lockout after 5 failed attempts
- ✅ **Email Verification** - Secure email change workflow
- ✅ **HIPAA Compliance** - Password policies, audit logging, 90-day rotation
- ✅ **2FA Ready** - Database support for two-factor authentication

### Multi-Tenant Architecture
- ✅ **Lab-Based Tenancy** - Each lab is an isolated tenant
- ✅ **Data Isolation** - Row-level security preventing cross-lab access
- ✅ **Role-Based Access Control** - System admin, lab admin, member, viewer
- ✅ **Flexible Memberships** - Users can belong to multiple labs

### Enterprise Features
- ✅ **Audit Logging** - Complete trail of all user actions
- ✅ **Email Notifications** - 7 types of security alerts
- ✅ **Login Tracking** - IP addresses, timestamps, success/failure
- ✅ **Password History** - Prevents reuse of last 5 passwords
- ✅ **Force Password Change** - Admin can require password updates

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [API Documentation](#-api-documentation)
- [Multi-Tenant Architecture](#-multi-tenant-architecture)
- [HIPAA Compliance](#-hipaa-compliance)
- [Security Features](#-security-features)
- [Django Integration](#-django-integration)
- [Production Deployment](#-production-deployment)
- [Testing](#-testing)
- [Tech Stack](#-tech-stack)

## ⚡ Quick Start

### 1. Clone and Setup

```powershell
# Clone repository
git clone https://github.com/zaidku/LHUMS.git
cd LHUMS

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy environment template
cp .env.example .env

# Edit .env and set your configuration
```

### 3. Initialize Database

```powershell
# Create database tables
python init_db.py

# Create admin user
python init_db.py create-admin
```

### 4. Run Server

```powershell
# Development
python run.py

# Production (with Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

Server runs at: `http://localhost:5000`

### 5. Test API

```powershell
python test_api.py
```

## 💾 Installation

### Prerequisites
- Python 3.8+ (tested on 3.13)
- pip
- Virtual environment (recommended)

### Detailed Setup

```powershell
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows PowerShell
# .venv\Scripts\activate.bat  # Windows CMD
# source .venv/bin/activate    # Unix/MacOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env

# 5. Initialize database
python init_db.py

# 6. Create admin user
python init_db.py create-admin
```

## 🔌 API Documentation

### Base URL
```
Development: http://localhost:5000/api
Production: https://your-domain.com/api
```

### Complete API Reference

See detailed documentation in:
- [FEATURES.md](FEATURES.md) - Complete feature list
- [QUICKSTART.md](QUICKSTART.md) - Quick examples
- API endpoint documentation below

### Authentication Endpoints (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register new user | No |
| POST | `/login` | Login and get tokens | No |
| POST | `/refresh` | Refresh access token | Yes (Refresh) |
| GET | `/me` | Get current user profile | Yes |
| POST | `/forgot-password` | Request password reset | No |
| POST | `/reset-password` | Reset password with token | No |
| POST | `/change-password` | Change password | Yes |
| POST | `/change-email` | Request email change | Yes |
| POST | `/verify-email` | Verify new email | No |
| GET | `/password-status` | Check password expiration | Yes |

### User Management Endpoints (`/api/users`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List all users (paginated) | Yes (Admin) |
| GET | `/<id>` | Get user by ID | Yes |
| PUT/PATCH | `/<id>` | Update user | Yes |
| DELETE | `/<id>` | Delete user | Yes (Admin) |
| GET | `/<id>/labs` | Get user's labs | Yes |
| POST | `/<id>/force-password-change` | Force password change | Yes (Admin) |
| POST | `/<id>/unlock` | Unlock account | Yes (Admin) |

### Lab Management Endpoints (`/api/labs`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List accessible labs | Yes |
| POST | `/` | Create lab | Yes (Admin) |
| GET | `/<id>` | Get lab details | Yes (Member) |
| PUT/PATCH | `/<id>` | Update lab | Yes (Admin) |
| DELETE | `/<id>` | Delete lab | Yes (Admin) |
| GET | `/<id>/members` | Get lab members | Yes (Member) |
| POST | `/<id>/members` | Add member | Yes (Lab Admin) |
| DELETE | `/<id>/members/<user_id>` | Remove member | Yes (Lab Admin) |
| PATCH | `/<id>/members/<user_id>/role` | Update role | Yes (Lab Admin) |

### Quick Examples

**Register:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@test.com","password":"pass123"}'
```

**Login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"pass123"}'
```

**Get Current User:**
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## 🏢 Multi-Tenant Architecture

### Overview

The UMS implements **lab-based multi-tenancy** with complete **data isolation**:

```
LinksHub Django Portal
  ├── Lab A (isolated)
  ├── Lab B (isolated)
  └── Lab C (isolated)
         ↓
    Flask UMS (Auth)
    • User Authentication
    • Lab Memberships
    • Data Isolation
    • Role Management
```

### Key Concepts

#### 1. Labs as Tenants
- Each **Lab** is a separate tenant with isolated data
- Labs have unique IDs, names, and codes
- Labs can be independently activated/deactivated

#### 2. User-Lab Memberships
- Users can belong to **multiple labs**
- Each membership has a **role**: `admin`, `member`, or `viewer`
- Memberships can be active or inactive

#### 3. Data Isolation ✅

**Enforced at Multiple Levels:**

```python
# Example: Adding lab-specific data
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lab_id = db.Column(db.Integer, db.ForeignKey('labs.id'), 
                       nullable=False, index=True)  # ✅ Required
    name = db.Column(db.String(100))

# Route with data isolation
@patients_bp.route('/labs/<int:lab_id>/patients')
@jwt_required()
@require_lab_access  # ✅ Verifies user is member of lab
def list_patients(lab_id):
    patients = Patient.query.filter_by(lab_id=lab_id).all()
    return jsonify({'patients': patients_schema.dump(patients)})
```

#### 4. Role-Based Access Control

**System-Level Roles:**
- **System Admin** - Full access to all labs
- **Regular User** - Access only to assigned labs

**Lab-Level Roles:**
- **Lab Admin** - Manage lab members and settings
- **Member** - Full access to lab data
- **Viewer** - Read-only access

### Access Control Decorators

```python
from app.utils.decorators import (
    admin_required,           # System admin only
    lab_admin_required,       # Lab admin or system admin
    require_lab_access,       # User must be lab member
    require_lab_role          # Require specific role
)

@app.route('/labs/<int:lab_id>/data')
@jwt_required()
@require_lab_access
def get_lab_data(lab_id):
    # User is guaranteed to be a member of this lab
    pass
```

For complete multi-tenant architecture documentation, see [MULTI_TENANT_ARCHITECTURE.md](MULTI_TENANT_ARCHITECTURE.md)

## 🔒 HIPAA Compliance

### Password Management

#### 90-Day Password Rotation ✅
- Automatic expiration after 90 days
- Expiration check on login
- Email warnings before expiration

#### Password History (Last 5) ✅
- Prevents reusing previous passwords
- Stored as hashed values
- Configurable history count

#### Password Complexity ✅
- Minimum 8 characters (configurable)
- PBKDF2-SHA256 hashing with salt
- Never stored in plain text

### Account Security

#### Automatic Account Lockout ✅
- Locks after 5 failed login attempts
- 30-minute lockout duration (configurable)
- Email notification sent
- Admin can manually unlock

#### Audit Logging ✅
Complete trail of all actions:
- User ID, action type
- IP address, user agent
- Timestamp, success/failure
- Additional details (JSON)

### HIPAA Configuration

```bash
# .env settings
PASSWORD_MIN_LENGTH=8
PASSWORD_EXPIRY_DAYS=90
PASSWORD_HISTORY_COUNT=5
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION=30
```

### HIPAA Checklist

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Password Expiration (90 days) | ✅ | `password_expires_at` field |
| Password History (last 5) | ✅ | `password_history` field |
| Minimum Length | ✅ | Configurable, default 8 |
| Account Lockout | ✅ | 5 attempts, 30-min duration |
| Audit Logging | ✅ | `audit_logs` table |
| User Notifications | ✅ | 7 email types |
| Admin Controls | ✅ | Force change, unlock |

For complete HIPAA compliance documentation, see [HIPAA_COMPLIANCE.md](HIPAA_COMPLIANCE.md)

## 🔐 Security Features

### Authentication
- **JWT Tokens**: Access token (1 hour) + Refresh token (30 days)
- **Password Hashing**: PBKDF2-SHA256 with unique salt
- **Token Expiration**: Automatic expiry and refresh

### Authorization
- **System Admin**: Full access to all resources
- **Lab Admin**: Manage specific lab and members
- **Member/Viewer**: Lab-specific access levels

### Data Protection
- **Input Validation**: Marshmallow schemas
- **SQL Injection Prevention**: SQLAlchemy ORM
- **XSS Protection**: Proper output encoding
- **CORS Configuration**: Restrict to allowed domains

### Monitoring
- **Login Tracking**: IP, timestamp, success/failure
- **Audit Logs**: Complete trail of actions
- **Email Alerts**: Security event notifications

## 🔗 Django Integration

### UMS Client Class

```python
# Use the provided UMSClient
from django_integration_example import UMSClient

# In your Django views
def login_view(request):
    ums = UMSClient('http://localhost:5000/api')
    
    result = ums.login(
        username=request.POST['username'],
        password=request.POST['password']
    )
    
    if 'access_token' in result:
        request.session['ums_access_token'] = result['access_token']
        request.session['ums_refresh_token'] = result['refresh_token']
        request.session['user_data'] = result['user']
        return redirect('dashboard')
    
    return render(request, 'login.html', {'error': 'Invalid credentials'})
```

See [django_integration_example.py](django_integration_example.py) for complete implementation.

## 🚀 Production Deployment

### Quick Production Setup

```bash
# 1. Database (PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost/ums_production

# 2. Application Server (Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# 3. Reverse Proxy (Nginx)
# Configure nginx to proxy to Gunicorn

# 4. SSL Certificate (Let's Encrypt)
sudo certbot --nginx -d ums.yourdomain.com
```

### Production Checklist

- [ ] Generate strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Configure SMTP email settings
- [ ] Enable HTTPS with SSL certificate
- [ ] Use Gunicorn/uWSGI (not Flask dev server)
- [ ] Set up Nginx reverse proxy
- [ ] Configure CORS for Django domain
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Set up systemd service
- [ ] Configure firewall rules
- [ ] Test all endpoints

For complete deployment guide, see [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

## 🧪 Testing

### Run Tests

```powershell
# Install pytest
pip install pytest pytest-flask

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_data_isolation.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Test API

```powershell
# Use provided test script
python test_api.py
```

### Data Isolation Tests

```python
# tests/test_data_isolation.py includes:
- test_user_can_only_see_their_labs()
- test_user_cannot_access_other_lab()
- test_user_cannot_see_other_lab_members()
- test_admin_can_access_all_labs()
- test_user_in_multiple_labs()
```

## 📚 Tech Stack

### Core
- **Flask 3.0.0** - Web framework
- **Python 3.13** - Programming language

### Authentication & Security
- **Flask-JWT-Extended 4.6.0** - JWT tokens
- **Werkzeug 3.0.1** - Password hashing
- **pyotp 2.9.0** - 2FA support

### Database
- **SQLAlchemy 2.0.25** - ORM
- **Flask-SQLAlchemy 3.1.1** - Flask integration
- **Flask-Migrate 4.0.5** - Migrations

### Validation
- **Marshmallow 3.22.0** - Schema validation
- **marshmallow-sqlalchemy 1.0.0** - SQLAlchemy integration

### Email & Notifications
- **Flask-Mail 0.10.0** - Email sending

### Integration
- **Flask-CORS 4.0.0** - CORS support
- **requests 2.32.3** - HTTP client

## 📖 Project Structure

```
LHUMS/
├── app/
│   ├── models/          # Database models
│   │   ├── user.py      # User (HIPAA-compliant)
│   │   ├── lab.py       # Lab & LabMembership
│   │   └── token.py     # Tokens & audit logs
│   ├── routes/          # API endpoints
│   │   ├── auth.py      # Authentication
│   │   ├── users.py     # User management
│   │   └── labs.py      # Lab management
│   ├── schemas/         # Validation schemas
│   └── utils/           # Utilities
│       ├── decorators.py       # Access control
│       ├── tenant_context.py   # Multi-tenant
│       ├── query_helpers.py    # Data isolation
│       ├── email_service.py    # Emails
│       └── audit.py            # Audit logging
├── config/              # Configuration
├── tests/               # Test suite
├── init_db.py          # Database init
├── run.py              # Entry point
└── requirements.txt    # Dependencies
```

## 📚 Documentation

- [README.md](README.md) - This file
- [FEATURES.md](FEATURES.md) - Complete feature list
- [HIPAA_COMPLIANCE.md](HIPAA_COMPLIANCE.md) - HIPAA documentation
- [MULTI_TENANT_ARCHITECTURE.md](MULTI_TENANT_ARCHITECTURE.md) - Multi-tenancy guide
- [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md) - Deployment guide
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) - Setup summary
- [django_integration_example.py](django_integration_example.py) - Django client

## 🤝 Contributing

```bash
# 1. Fork the repository
git clone https://github.com/YOUR_USERNAME/LHUMS.git

# 2. Create feature branch
git checkout -b feature/your-feature

# 3. Make changes and test
pytest tests/ -v

# 4. Commit and push
git commit -m "Add: your feature"
git push origin feature/your-feature

# 5. Create pull request
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: https://github.com/zaidku/LHUMS/issues
- **Documentation**: See docs in repository

## 📝 Changelog

### Version 1.0 (2025-11-05)

**Features:**
- ✅ JWT-based authentication
- ✅ HIPAA-compliant password policies
- ✅ Multi-tenant architecture with data isolation
- ✅ Role-based access control
- ✅ Email notifications
- ✅ Audit logging
- ✅ Account security features
- ✅ Django integration client
- ✅ Comprehensive test suite

**Security:**
- Password hashing with PBKDF2-SHA256
- JWT token expiration and refresh
- SQL injection prevention
- Account lockout mechanism
- Email verification workflow

**Multi-Tenancy:**
- Lab-based tenant isolation
- User-lab membership management
- Role-based permissions per lab
- Data isolation at query level

---

**Made for LinksHub Portal**

**Version 1.0** | **Released: November 1, 2025** | **[GitHub](https://github.com/zaidku/LHUMS)**
