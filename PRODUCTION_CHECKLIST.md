# Production Readiness Checklist

## ✅ What's Already Done

- [x] Complete Flask application structure
- [x] JWT authentication system
- [x] Database models and relationships
- [x] Input validation with Marshmallow
- [x] Password hashing (Werkzeug)
- [x] Role-based access control
- [x] RESTful API endpoints
- [x] Error handling
- [x] Development environment setup

## ⚠️ Required for Production

### 1. Security Configuration

- [ ] **Generate Strong Secret Keys**
  ```powershell
  # Generate secure random keys
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
  Add to `.env`:
  ```
  SECRET_KEY=<generated-key>
  JWT_SECRET_KEY=<another-generated-key>
  ```

- [ ] **Configure CORS Properly**
  Edit `app/__init__.py` to add:
  ```python
  from flask_cors import CORS
  CORS(app, origins=['https://your-django-domain.com'])
  ```

- [ ] **Use Environment Variables**
  - Never hardcode secrets in code
  - Use `.env` file or environment variables
  - Never commit `.env` to git

### 2. Database

- [ ] **Switch to Production Database**
  
  Current: SQLite (good for dev, NOT for production)
  
  **Recommended: PostgreSQL**
  ```bash
  # Install PostgreSQL driver
  pip install psycopg2-binary
  
  # Update .env
  DATABASE_URL=postgresql://username:password@localhost:5432/ums_db
  ```
  
  **Or MySQL:**
  ```bash
  pip install pymysql
  DATABASE_URL=mysql+pymysql://username:password@localhost:3306/ums_db
  ```

- [ ] **Database Migrations**
  
  Add Flask-Migrate properly:
  ```bash
  flask db init
  flask db migrate -m "Initial migration"
  flask db upgrade
  ```

- [ ] **Database Backups**
  - Set up automated backups
  - Test restore procedures

### 3. Application Server

- [ ] **Use Production WSGI Server**
  
  Don't use Flask's development server!
  
  **Option 1: Gunicorn (Recommended)**
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 run:app
  ```
  
  **Option 2: uWSGI**
  ```bash
  pip install uwsgi
  uwsgi --http :5000 --wsgi-file run.py --callable app
  ```

- [ ] **Configure Workers**
  - Formula: `(2 x CPU cores) + 1`
  - Monitor memory usage
  - Use process manager (systemd/supervisor)

### 4. Reverse Proxy

- [ ] **Set up Nginx/Apache**
  
  **Example Nginx config:**
  ```nginx
  server {
      listen 80;
      server_name ums.yourdomain.com;
      
      location / {
          proxy_pass http://127.0.0.1:5000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  ```

### 5. HTTPS/SSL

- [ ] **Install SSL Certificate**
  - Use Let's Encrypt (free)
  - Or commercial SSL certificate
  
  ```bash
  # Let's Encrypt with certbot
  sudo certbot --nginx -d ums.yourdomain.com
  ```

- [ ] **Force HTTPS**
  - Redirect all HTTP to HTTPS
  - Set secure cookie flags

### 6. Logging

- [ ] **Configure Production Logging**
  
  Add to `app/__init__.py`:
  ```python
  import logging
  from logging.handlers import RotatingFileHandler
  
  if not app.debug:
      file_handler = RotatingFileHandler('logs/ums.log', maxBytes=10240000, backupCount=10)
      file_handler.setFormatter(logging.Formatter(
          '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
      ))
      file_handler.setLevel(logging.INFO)
      app.logger.addHandler(file_handler)
      app.logger.setLevel(logging.INFO)
  ```

- [ ] **Set up Log Rotation**
- [ ] **Monitor Error Logs**

### 7. Monitoring & Health Checks

- [ ] **Add Health Check Endpoint**
  
  Create `app/routes/health.py`:
  ```python
  from flask import Blueprint, jsonify
  from app import db
  
  health_bp = Blueprint('health', __name__)
  
  @health_bp.route('/health', methods=['GET'])
  def health_check():
      try:
          # Check database connection
          db.session.execute('SELECT 1')
          return jsonify({'status': 'healthy', 'database': 'connected'}), 200
      except Exception as e:
          return jsonify({'status': 'unhealthy', 'error': str(e)}), 503
  ```

- [ ] **Set up Monitoring**
  - Use tools like: New Relic, DataDog, Sentry
  - Monitor response times
  - Track error rates
  - Alert on failures

### 8. Performance

- [ ] **Database Connection Pooling**
  
  Add to `config/config.py`:
  ```python
  SQLALCHEMY_ENGINE_OPTIONS = {
      'pool_size': 10,
      'pool_recycle': 3600,
      'pool_pre_ping': True
  }
  ```

- [ ] **Enable Caching**
  - Use Redis for session storage
  - Cache frequently accessed data
  - Set proper cache headers

- [ ] **Rate Limiting**
  
  Install Flask-Limiter:
  ```bash
  pip install Flask-Limiter
  ```
  
  Add to `app/__init__.py`:
  ```python
  from flask_limiter import Limiter
  from flask_limiter.util import get_remote_address
  
  limiter = Limiter(
      app,
      key_func=get_remote_address,
      default_limits=["200 per day", "50 per hour"]
  )
  ```

### 9. Security Hardening

- [ ] **Security Headers**
  
  Install Flask-Talisman:
  ```bash
  pip install flask-talisman
  ```
  
  Add to `app/__init__.py`:
  ```python
  from flask_talisman import Talisman
  Talisman(app, force_https=True)
  ```

- [ ] **Input Sanitization**
  - Already done with Marshmallow ✓
  - Add additional XSS protection if needed

- [ ] **SQL Injection Protection**
  - Already using SQLAlchemy ORM ✓
  - Never use raw SQL queries

- [ ] **CSRF Protection** (if using forms)

- [ ] **JWT Token Security**
  - Current token expiry: 1 hour (access), 30 days (refresh) ✓
  - Consider shorter refresh token lifetime
  - Implement token blacklist for logout

### 10. Testing

- [ ] **Write Unit Tests**
  ```bash
  pytest tests/
  ```

- [ ] **Integration Tests**
  - Test all API endpoints
  - Test authentication flows
  - Test role-based access

- [ ] **Load Testing**
  - Use tools: Apache Bench, Locust, K6
  - Test under expected load
  - Identify bottlenecks

### 11. Documentation

- [ ] **API Documentation**
  - Consider adding Swagger/OpenAPI
  - Document all endpoints
  - Provide example requests/responses

- [ ] **Deployment Documentation**
  - Server setup instructions
  - Environment variables
  - Backup/restore procedures

### 12. Deployment

- [ ] **Process Manager**
  
  **Systemd service example:**
  ```ini
  [Unit]
  Description=Flask UMS
  After=network.target
  
  [Service]
  User=www-data
  WorkingDirectory=/var/www/ums
  Environment="PATH=/var/www/ums/.venv/bin"
  ExecStart=/var/www/ums/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
  Restart=always
  
  [Install]
  WantedBy=multi-user.target
  ```

- [ ] **Firewall Configuration**
  - Only expose necessary ports
  - Use security groups (if cloud)

- [ ] **Auto-restart on Failure**

### 13. Django Integration

- [ ] **Configure CORS for Django Domain**
  ```python
  CORS(app, origins=['https://your-django-app.com'])
  ```

- [ ] **Share Session/Token Strategy**
  - Decide where to store JWT tokens (Django session/cookies)
  - Handle token refresh in Django

- [ ] **Error Handling**
  - Handle UMS downtime gracefully in Django
  - Implement circuit breaker pattern

### 14. Compliance & Legal

- [ ] **GDPR Compliance** (if EU users)
  - User data export
  - Right to be forgotten (delete user)
  - Privacy policy

- [ ] **Password Policy**
  - Minimum length enforcement
  - Password complexity rules
  - Password expiration

- [ ] **Audit Logging**
  - Log user actions
  - Log admin actions
  - Keep audit trail

### 15. DevOps

- [ ] **Version Control**
  - Already using Git ✓
  - Create production branch
  - Tag releases

- [ ] **CI/CD Pipeline**
  - Automated testing
  - Automated deployment
  - Use GitHub Actions, GitLab CI, or Jenkins

- [ ] **Container Deployment** (Optional)
  
  Create `Dockerfile`:
  ```dockerfile
  FROM python:3.12-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
  ```

## 📝 Production Configuration Example

### `.env` for Production

```bash
FLASK_ENV=production
FLASK_DEBUG=False

# Security - MUST CHANGE
SECRET_KEY=<generate-strong-key>
JWT_SECRET_KEY=<generate-strong-key>

# Database - PostgreSQL
DATABASE_URL=postgresql://ums_user:secure_password@localhost:5432/ums_production

# CORS
ALLOWED_ORIGINS=https://your-django-app.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ums/app.log

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379
```

### `requirements-prod.txt`

```txt
# Production requirements
gunicorn==21.2.0
psycopg2-binary==2.9.9
redis==5.0.1
flask-limiter==3.5.0
flask-talisman==1.1.0
sentry-sdk[flask]==1.39.1
```

## 🚦 Deployment Checklist

Before going live:

1. [ ] All security configurations applied
2. [ ] Production database configured
3. [ ] SSL certificate installed
4. [ ] Environment variables set
5. [ ] Logs configured and working
6. [ ] Monitoring/alerts set up
7. [ ] Backups configured
8. [ ] Load testing completed
9. [ ] Security audit completed
10. [ ] Documentation updated
11. [ ] Rollback plan prepared
12. [ ] Support team trained

## 📊 Estimated Timeline

- **Minimal Production Setup**: 1-2 days
  - Database, HTTPS, Gunicorn, basic security
  
- **Full Production Setup**: 1-2 weeks
  - All monitoring, logging, testing, hardening

## 🎯 Quick Production Setup (Minimal)

For a quick production deployment:

```bash
# 1. Install production dependencies
pip install gunicorn psycopg2-binary

# 2. Set environment variables
export FLASK_ENV=production
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export DATABASE_URL=postgresql://user:pass@localhost/ums_db

# 3. Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# 4. Set up Nginx reverse proxy with SSL
# 5. Configure systemd service
```

## ⚠️ Critical Items (Do These First)

1. **Change SECRET_KEY and JWT_SECRET_KEY** - Critical security issue
2. **Use Production Database** - SQLite won't handle concurrent users
3. **Enable HTTPS** - Never send passwords over HTTP
4. **Use Gunicorn/uWSGI** - Flask dev server is not production-safe
5. **Configure CORS Properly** - Only allow your Django domain

---

**Bottom Line**: The code is production-quality, but the **configuration** needs work. You have a solid foundation that needs proper deployment setup.
