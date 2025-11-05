# Flask User Management Service (UMS) - Setup Complete! 🎉

## What Has Been Created

User Management Service is fully set up and ready to use!

### ✅ Complete Project Structure

```
LHUMS/
├── app/                          # Main application package
│   ├── __init__.py              # Flask app factory
│   ├── models/                  # Database models
│   │   ├── user.py             # User model with authentication
│   │   └── lab.py              # Lab and LabMembership models
│   ├── routes/                  # API endpoints
│   │   ├── auth.py             # /api/auth/* (register, login, refresh, me)
│   │   ├── users.py            # /api/users/* (CRUD operations)
│   │   └── labs.py             # /api/labs/* (lab management)
│   ├── schemas/                 # Marshmallow validation schemas
│   │   ├── user_schema.py      # User serialization
│   │   └── lab_schema.py       # Lab serialization
│   └── utils/                   # Utilities
│       └── decorators.py        # @admin_required, @lab_admin_required
├── config/
│   └── config.py               # Environment configurations
├── .venv/                       # Python virtual environment (configured)
├── init_db.py                  # Database initialization script
├── run.py                      # Application entry point
├── test_api.py                 # API testing script
├── django_integration_example.py # Django integration client
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # Complete documentation
├── QUICKSTART.md              # Quick start guide
└── PYTHON_313_NOTES.md        # Python 3.13 compatibility notes
```

### ✅ Installed Dependencies

All packages are installed in your virtual environment (`.venv`):
- Flask 3.0.0
- Flask-JWT-Extended (JWT authentication)
- Flask-SQLAlchemy (Database ORM)
- Flask-Marshmallow (Data validation)
- SQLAlchemy 2.1.0 (Python 3.13 compatible dev version)
- Flask-CORS (for Django integration)
- And more...

### ✅ Database Initialized

The SQLite database (`ums_dev.db`) has been created with 3 tables:
- **users** - User accounts with authentication
- **labs** - Laboratory/tenant entities
- **lab_memberships** - User-lab relationships with roles

### ✅ Key Features Implemented

1. **Authentication System**
   - User registration with password hashing
   - JWT-based login (access + refresh tokens)
   - Token refresh mechanism
   - Protected endpoints

2. **User Management**
   - Create, read, update, delete users
   - User profiles with first/last names
   - Active/inactive status
   - Admin vs regular user roles

3. **Multi-Lab Support**
   - Create and manage multiple labs
   - Assign users to labs
   - Role-based access (admin, member, viewer)
   - Lab-specific permissions

4. **Security**
   - Password hashing (Werkzeug)
   - JWT token authentication
   - Role-based access control
   - Input validation (Marshmallow)

## 🚀 Next Steps

### 1. Create Your First Admin User

```powershell
python init_db.py create-admin
```

### 2. Start the Development Server

```powershell
python run.py
```

The API will be available at `http://localhost:5000`

### 3. Test the API

Use the provided test script:
```powershell
python test_api.py
```

Or test manually with curl (see QUICKSTART.md for examples)

### 4. Integrate with Django

See `django_integration_example.py` for a ready-to-use client class that you can import into your Django project:

```python
from ums_client import UMSClient

# In your Django view
ums = UMSClient('http://localhost:5000/api')
result = ums.login(username, password)
```

## 📚 Documentation

- **README.md** - Complete API documentation and usage guide
- **QUICKSTART.md** - Quick start guide with common commands
- **PYTHON_313_NOTES.md** - Python 3.13 compatibility information
- **django_integration_example.py** - Django integration examples

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///ums_dev.db
```

### Production Deployment

1. Set `FLASK_ENV=production`
2. Use a production database (PostgreSQL/MySQL)
3. Set strong secret keys
4. Use Gunicorn or uWSGI
5. Set up Nginx as reverse proxy
6. Enable HTTPS
7. Configure CORS for your Django domain

## 🎯 API Endpoints Overview

### Authentication (`/api/auth`)
- POST `/register` - Register new user
- POST `/login` - Login and get tokens
- POST `/refresh` - Refresh access token
- GET `/me` - Get current user profile

### Users (`/api/users`)
- GET `/` - List all users (admin only, paginated)
- GET `/<id>` - Get user by ID
- PUT/PATCH `/<id>` - Update user
- DELETE `/<id>` - Delete user (admin only)
- GET `/<id>/labs` - Get user's labs

### Labs (`/api/labs`)
- GET `/` - List all labs
- POST `/` - Create lab (admin only)
- GET `/<id>` - Get lab by ID
- PUT/PATCH `/<id>` - Update lab (admin only)
- DELETE `/<id>` - Delete lab (admin only)
- GET `/<id>/members` - Get lab members
- POST `/<id>/members` - Add member to lab
- DELETE `/<id>/members/<user_id>` - Remove member
- PATCH `/<id>/members/<user_id>/role` - Update member role

## 🔐 Authentication Flow

1. **Register**: `POST /api/auth/register` → Get user data
2. **Login**: `POST /api/auth/login` → Get `access_token` and `refresh_token`
3. **Use API**: Include `Authorization: Bearer <access_token>` header
4. **Refresh**: When token expires, `POST /api/auth/refresh` with refresh token

## 🌟 Django Integration Pattern

```python
# In your Django views.py
from ums_client import UMSClient

def my_view(request):
    ums = UMSClient()
    
    # Authenticate
    result = ums.login(username, password)
    request.session['ums_token'] = result['access_token']
    
    # Get user data
    user = ums.get_current_user()
    
    # Get user's labs
    labs = ums.get_user_labs(user['user']['id'])
    
    return render(request, 'template.html', {
        'user': user,
        'labs': labs
    })
```

## 📝 Common Commands

```powershell
# Start server
python run.py

# Initialize database
python init_db.py

# Create admin
python init_db.py create-admin

# Test API
python test_api.py

# Reset database
Remove-Item ums_dev.db
python init_db.py

# Install dependencies
pip install -r requirements.txt

# Check database
python -c "from app import create_app, db; from app.models import User; app = create_app(); app.app_context().push(); print(User.query.all())"
```

## ⚠️ Important Notes

### Python 3.13 Compatibility
You're using Python 3.13. We've installed the development version of SQLAlchemy that has the Python 3.13 compatibility fix. See `PYTHON_313_NOTES.md` for details.

### Security
- Change `SECRET_KEY` and `JWT_SECRET_KEY` in production
- Never commit `.env` file
- Use HTTPS in production
- Configure CORS properly for your Django domain

### Database
- Current setup uses SQLite (good for development)
- For production, use PostgreSQL or MySQL
- Migrations can be added using Flask-Migrate (if needed)

## 🤝 Support

The UMS is fully functional and ready for integration with your Django webapp portal. Each lab in your Django app can now authenticate users through this centralized service.

## ✨ What Makes This Special

- **Multi-tenant ready**: One UMS for all your labs
- **Secure**: Industry-standard JWT authentication
- **Flexible**: Role-based access control per lab
- **Django-friendly**: Easy integration with Django
- **Well-documented**: Complete API documentation
- **Production-ready**: Just needs configuration

---

