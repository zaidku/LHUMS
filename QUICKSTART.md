# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Initialize the Database

```powershell
python init_db.py
```

### 2. Create an Admin User

```powershell
python init_db.py create-admin
```

Enter the required information when prompted.

### 3. Start the Server

```powershell
python run.py
```

The API will be available at `http://localhost:5000`

### 4. Test the API

#### Register a New User

```powershell
curl -X POST http://localhost:5000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

#### Login

```powershell
curl -X POST http://localhost:5000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

Save the `access_token` from the response.

#### Get Current User Profile

```powershell
curl -X GET http://localhost:5000/api/auth/me `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Create a Lab (Admin Only)

```powershell
curl -X POST http://localhost:5000/api/labs `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" `
  -d '{
    "name": "Test Lab",
    "code": "TESTLAB",
    "description": "A test laboratory"
  }'
```

#### List All Labs

```powershell
curl -X GET http://localhost:5000/api/labs `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Next Steps

- See `README.md` for complete API documentation
- See `PYTHON_313_NOTES.md` for Python 3.13 compatibility notes
- Integrate with your Django webapp using HTTP requests
- Configure CORS for your Django domain
- Set up environment variables for production

## Common Tasks

### Reset Database

```powershell
Remove-Item ums_dev.db
python init_db.py
python init_db.py create-admin
```

### Check Database

```powershell
python -c "from app import create_app, db; from app.models import User, Lab; app = create_app(); app.app_context().push(); print(f'Users: {User.query.count()}'); print(f'Labs: {Lab.query.count()}')"
```

### Run in Development Mode

```powershell
$env:FLASK_ENV="development"
python run.py
```

### Run in Production Mode

```powershell
$env:FLASK_ENV="production"
$env:SECRET_KEY="your-production-secret-key"
$env:DATABASE_URL="postgresql://user:pass@localhost/dbname"
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```
