# 🔐 Auth Microservice

A production-ready authentication microservice built with **FastAPI**, featuring JWT tokens, user management, token blacklisting, and automatic cleanup mechanisms.

## ✨ Features

- ✅ **User Registration** with comprehensive password validation
- ✅ **JWT Authentication** with separate access and refresh tokens
- ✅ **Token Refresh** mechanism for seamless user experience
- ✅ **Secure Logout** with token blacklisting
- ✅ **Automatic Token Cleanup** - Background task removes expired tokens hourly
- ✅ **Rate Limiting** to prevent brute force attacks (10 requests/minute)
- ✅ **CORS Support** for frontend integration
- ✅ **PostgreSQL Database** with SQLAlchemy 2.0 ORM
- ✅ **Unlimited Password Length Support** - SHA-256 + bcrypt for passwords of any length
- ✅ **Comprehensive Logging** for security events and monitoring
- ✅ **Health Check** endpoint with database connectivity verification
- ✅ **Interactive API Documentation** with Swagger UI and ReDoc
- ✅ **Pydantic v2 Validation** for all inputs and outputs
- ✅ **Service Layer Architecture** for clean, maintainable code

## 📁 Project Structure

```
auth/
├── main.py                    # FastAPI application and API endpoints
├── auth_service.py           # Authentication business logic layer
├── database.py               # SQLAlchemy models and database configuration
├── models.py                 # Pydantic schemas for validation
├── config.py                 # Settings management with Pydantic Settings
├── background_tasks.py       # Background cleanup tasks
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .env                     # Your environment variables (DO NOT COMMIT)
├── README.md                # This file
└── CLEANUP_DEPLOYMENT.md    # Token cleanup deployment guide
```

## 🚀 Quick Start Guide

Follow these steps to set up the project on your local machine after downloading the files.

### Prerequisites

- **Python 3.11+** (3.13 recommended)
- **PostgreSQL 14+** (16 recommended)
- **pip** (Python package manager)
- **virtualenv** (optional but recommended)

### Step 1: Verify Python Installation

```bash
python3 --version
# Should show Python 3.11.0 or higher
```

If Python is not installed:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# macOS (using Homebrew)
brew install python@3.11

# Verify installation
python3 --version
pip3 --version
```

### Step 2: Set Up Virtual Environment

```bash
# Navigate to project directory
cd /path/to/auth

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Your prompt should now show (.venv)
```

### Step 3: Install Python Dependencies

```bash
# Make sure virtual environment is activated
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- fastapi (0.120.4)
- uvicorn (0.38.0)
- sqlalchemy (2.0.44)
- psycopg2-binary (2.9.11)
- python-jose (3.5.0)
- bcrypt (5.0.0)
- pydantic-settings (2.11.0)
- email-validator (2.3.0)

### Step 4: Install and Configure PostgreSQL

#### Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS (using Homebrew)
brew install postgresql@16
brew services start postgresql@16

# Verify PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Check PostgreSQL version
psql --version
```

#### Create Database and User

```bash
# Switch to postgres user (Linux)
sudo -u postgres psql

# Or directly connect (macOS)
psql postgres

# Now in PostgreSQL shell, run these commands:
```

```sql
-- Create database
CREATE DATABASE auth_db;

-- Create user with password
CREATE USER auth_user WITH PASSWORD 'your_secure_password_here';

-- Grant privileges on database
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;

-- Connect to the auth_db database
\c auth_db

-- Grant schema permissions (required for PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO auth_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO auth_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO auth_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO auth_user;

-- Verify grants
\l auth_db
\du auth_user

-- Exit PostgreSQL
\q
```

#### Verify Database Connection

```bash
# Test connection with your credentials
psql -h localhost -U auth_user -d auth_db

# If prompted for password, enter: your_secure_password_here
# If connection successful, you'll see: auth_db=>

# Test a query
SELECT current_database(), current_user;

# Exit
\q
```

### Step 5: Configure Environment Variables

```bash
# Create .env file from example
cp .env.example .env

# Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# This will output something like:
# a5f03e023c81ec010f881e07b86e1ff3f2e6eec7eeb189a5a257ddffc76cf925
```

Now edit `.env` file with your favorite editor:

```bash
nano .env  # or vim .env, or code .env
```

**Update these critical values:**

```bash
# REQUIRED: Use the secret key you just generated
SECRET_KEY=a5f03e023c81ec010f881e07b86e1ff3f2e6eec7eeb189a5a257ddffc76cf925

# REQUIRED: Update with your PostgreSQL credentials
DATABASE_URL=postgresql://auth_user:your_secure_password_here@localhost:5432/auth_db

# Optional: Customize these settings
PROJECT_NAME=Auth Microservice
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS origins (must be JSON array format)
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Rate limiting
RATE_LIMIT_PER_MINUTE=10

# Environment
ENVIRONMENT=development
DEBUG=True
```

**⚠️ IMPORTANT NOTES:**

1. **SECRET_KEY**: Must be at least 32 characters. Never use the example value in production!
2. **DATABASE_URL**: Replace `your_secure_password_here` with your actual PostgreSQL password
3. **CORS_ORIGINS**: Must be in JSON array format: `["url1","url2"]` (no spaces after commas)

### Step 6: Initialize the Database

```bash
# Activate virtual environment if not already activated
source .venv/bin/activate

# Initialize database tables
python3 -c "from database import init_db; init_db()"

# Verify tables were created
psql -h localhost -U auth_user -d auth_db -c "\dt"

# Should show:
#              List of relations
#  Schema |      Name       | Type  |   Owner   
# --------+-----------------+-------+-----------
#  public | token_blacklist | table | auth_user
#  public | users           | table | auth_user
```

### Step 7: Verify Configuration

```bash
# Test that settings load correctly
python3 -c "from config import get_settings; s = get_settings(); print('✅ Config loaded'); print(f'Database: {s.database_url.split(\"@\")[1]}'); print(f'CORS Origins: {s.cors_origins}')"

# Should output:
# ✅ Config loaded
# Database: localhost:5432/auth_db
# CORS Origins: ['http://localhost:3000', 'http://localhost:8080']
```

### Step 8: Run the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
# INFO:     Database initialized
# INFO:     Startup cleanup: removed 0 expired tokens
# INFO:     Background token cleanup task started
```

### Step 9: Verify Everything Works

Open a new terminal and test the API:

```bash
# Test health check
curl http://localhost:8000/health

# Should return:
# {"message":"healthy","detail":"Service and database are operational"}

# Test API root
curl http://localhost:8000/

# Should return:
# {"service":"Auth Microservice","version":"1.0.0","docs":"/docs","health":"/health"}

# Open browser and check documentation
# Visit: http://localhost:8000/docs
```

🎉 **Congratulations!** Your auth microservice is now running!

## 📚 API Documentation

Once running, access interactive documentation:

- **Swagger UI**: http://localhost:8000/docs (try API calls directly)
- **ReDoc**: http://localhost:8000/redoc (clean documentation view)
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔑 API Endpoints

### Public Endpoints (No Authentication Required)

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | `/api/v1/register`    | Register a new user            |
| POST   | `/api/v1/login`       | Login (get tokens)             |
| POST   | `/api/v1/refresh`     | Refresh access token           |
| GET    | `/health`             | Health check                   |
| GET    | `/`                   | API information                |

### Protected Endpoints (Requires Authentication)

| Method | Endpoint                      | Description                    |
|--------|-------------------------------|--------------------------------|
| GET    | `/api/v1/users/me`            | Get current user info          |
| POST   | `/api/v1/logout`              | Logout (blacklist token)       |
| POST   | `/api/v1/admin/cleanup-tokens`| Manually cleanup expired tokens|

## 💡 Usage Examples

### 1️⃣ Register a New User

```bash
curl -X POST "http://localhost:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "disabled": false
}
```

**Password Requirements:**
- ✅ Minimum 8 characters, maximum 128 characters
- ✅ At least one uppercase letter (A-Z)
- ✅ At least one lowercase letter (a-z)
- ✅ At least one digit (0-9)
- ✅ Supports unlimited length passwords via SHA-256 pre-hashing

### 2️⃣ Login (Get Tokens)

```bash
curl -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=SecurePass123"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNzYyMTY0MDAwLCJ0eXBlIjoiYWNjZXNzIn0...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNzYyNzY4MDAwLCJ0eXBlIjoicmVmcmVzaCJ9...",
  "token_type": "bearer"
}
```

**Token Expiration:**
- Access Token: 30 minutes (default)
- Refresh Token: 7 days (default)

### 3️⃣ Access Protected Endpoint

```bash
# Save your access token
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Get current user info
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "disabled": false
}
```

### 4️⃣ Refresh Access Token

```bash
# When access token expires, use refresh token
REFRESH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST "http://localhost:8000/api/v1/refresh?refresh_token=$REFRESH_TOKEN"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 5️⃣ Logout (Blacklist Token)

```bash
curl -X POST "http://localhost:8000/api/v1/logout" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Response:**
```json
{
  "message": "Successfully logged out",
  "detail": "Token has been revoked"
}
```

**Note:** After logout, the token is blacklisted and cannot be used again. It will be automatically cleaned up after expiration.

## ⚙️ Configuration Reference

All settings are managed via environment variables in `.env`:

| Variable                      | Type   | Required | Default                    | Description                                   |
|-------------------------------|--------|----------|----------------------------|-----------------------------------------------|
| `SECRET_KEY`                  | string | ✅ Yes   | -                          | Secret key for JWT (min 32 chars)             |
| `ALGORITHM`                   | string | No       | `HS256`                    | JWT signing algorithm                         |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int    | No       | `30`                       | Access token lifetime in minutes              |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | int    | No       | `7`                        | Refresh token lifetime in days                |
| `DATABASE_URL`                | string | ✅ Yes   | -                          | PostgreSQL connection string                  |
| `API_V1_PREFIX`               | string | No       | `/api/v1`                  | API version prefix                            |
| `PROJECT_NAME`                | string | No       | `Auth Microservice`        | Project name for docs                         |
| `CORS_ORIGINS`                | array  | No       | `["http://localhost:3000"]`| Allowed CORS origins (JSON array format)      |
| `RATE_LIMIT_PER_MINUTE`       | int    | No       | `10`                       | Login rate limit per minute                   |
| `ENVIRONMENT`                 | string | No       | `development`              | Environment (development/production/testing)  |
| `DEBUG`                       | bool   | No       | `True`                     | Debug mode (SQL logging)                      |

### Database Connection String Format

```
postgresql://username:password@host:port/database_name

Examples:
  Local:  postgresql://auth_user:pass123@localhost:5432/auth_db
  Remote: postgresql://user:pass@db.example.com:5432/auth_db
  SSL:    postgresql://user:pass@host:5432/db?sslmode=require
```

### CORS Configuration

**Important:** `CORS_ORIGINS` must be a valid JSON array in `.env`:

```bash
# ✅ Correct format
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# ❌ Wrong format (will fail)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 🛡️ Security Features

### Password Security
- **SHA-256 Pre-hashing**: Supports unlimited password lengths
- **Bcrypt Hashing**: Industry-standard with automatic salt generation (12 rounds)
- **Validation**: Enforces strong password requirements

### Token Security
- **JWT Tokens**: Cryptographically signed with HS256
- **Token Types**: Separate access and refresh tokens
- **Expiration**: Automatic token expiration
- **Blacklisting**: Revoked tokens are permanently blacklisted
- **Automatic Cleanup**: Background task removes expired tokens hourly

### Application Security
- **Rate Limiting**: 10 requests/minute on login endpoint
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic v2 validates all inputs
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **Logging**: Comprehensive security event logging

## 🧹 Automatic Token Cleanup

The application includes an automatic cleanup mechanism for expired tokens:

### How It Works

1. **Background Task**: Runs every hour to delete expired tokens
2. **Startup Cleanup**: Removes expired tokens on application start
3. **Manual Endpoint**: Admin can trigger cleanup via API

### Monitoring Cleanup

Check application logs:

```bash
# Watch logs for cleanup activity
tail -f /path/to/logs

# You'll see messages like:
# INFO - Running token cleanup task...
# INFO - Cleaned up 42 expired tokens from blacklist
```

### Manual Cleanup

```bash
curl -X POST "http://localhost:8000/api/v1/admin/cleanup-tokens" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

For detailed cleanup deployment information, see `CLEANUP_DEPLOYMENT.md`.

## 🔧 Development

### Running in Development Mode

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Run with debug logging
uvicorn main:app --reload --log-level debug
```

### Database Management

```bash
# View database tables
psql -h localhost -U auth_user -d auth_db -c "\dt"

# View users
psql -h localhost -U auth_user -d auth_db -c "SELECT username, email, disabled FROM users;"

# View blacklisted tokens count
psql -h localhost -U auth_user -d auth_db -c "SELECT COUNT(*) FROM token_blacklist;"

# View expired tokens
psql -h localhost -U auth_user -d auth_db -c "SELECT COUNT(*) FROM token_blacklist WHERE expires_at < NOW();"

# Clear all blacklisted tokens (for testing)
psql -h localhost -U auth_user -d auth_db -c "TRUNCATE token_blacklist;"
```

### Environment Management

```bash
# Switch to production
# Edit .env:
ENVIRONMENT=production
DEBUG=False

# Use stronger settings
ACCESS_TOKEN_EXPIRE_MINUTES=15
RATE_LIMIT_PER_MINUTE=5
```

## 🚀 Production Deployment

### Prerequisites for Production

1. **Secure Secret Key**: Generate a strong 64+ character key
2. **Production Database**: Use managed PostgreSQL (AWS RDS, DigitalOcean, etc.)
3. **HTTPS**: Use reverse proxy (nginx/Apache) with SSL certificates
4. **Environment Variables**: Never commit `.env` to version control

### Production Configuration

```bash
# .env for production
SECRET_KEY=<generate-strong-64-char-key>
ENVIRONMENT=production
DEBUG=False

# Use stricter settings
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=3
RATE_LIMIT_PER_MINUTE=5

# Production database
DATABASE_URL=postgresql://user:pass@prod-db.example.com:5432/auth_db

# Production CORS
CORS_ORIGINS=["https://yourdomain.com"]
```

### Running with Systemd (Linux)

Create `/etc/systemd/system/auth-service.service`:

```ini
[Unit]
Description=Auth Microservice
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/auth
Environment="PATH=/var/www/auth/.venv/bin"
ExecStart=/var/www/auth/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable auth-service
sudo systemctl start auth-service
sudo systemctl status auth-service
```

### Running with Multiple Workers

```bash
# Production: 4 workers (adjust based on CPU cores)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Rule of thumb: workers = (2 * CPU_CORES) + 1
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name auth.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Production Database Configuration

- Enable connection pooling (already configured in `database.py`)
- Set up automated backups
- Enable SSL connections
- Use read replicas for scaling
- Monitor query performance

## 🐛 Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'X'"

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. "Could not connect to database"

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list                # macOS

# Verify connection string in .env
DATABASE_URL=postgresql://auth_user:password@localhost:5432/auth_db

# Test connection
psql -h localhost -U auth_user -d auth_db
```

#### 3. "Column token_blacklist.expires_at does not exist"

This means you need to run database initialization:

```bash
# Drop and recreate tables (development only!)
python3 -c "from database import Base, engine; Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)"
```

#### 4. "CORS_ORIGINS parsing error"

Make sure `.env` has correct JSON array format:

```bash
# ✅ Correct
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# ❌ Wrong
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### 5. "Rate limit exceeded"

Wait 60 seconds or increase the limit in `.env`:

```bash
RATE_LIMIT_PER_MINUTE=20
```

### Logging

Check logs for detailed error information:

```bash
# Application logs (if running in terminal)
# Will show in stdout

# For systemd service
sudo journalctl -u auth-service -f

# For production, consider using log files
uvicorn main:app --log-config logging.json
```

## 📋 Testing

### Manual Testing Workflow

```bash
# 1. Register user
curl -X POST "http://localhost:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","full_name":"Test User","password":"Test1234"}'

# 2. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=Test1234" | jq -r .access_token)

# 3. Access protected endpoint
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"

# 4. Logout
curl -X POST "http://localhost:8000/api/v1/logout" \
  -H "Authorization: Bearer $TOKEN"

# 5. Try to use token after logout (should fail)
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

## 📦 Dependencies

Main dependencies and their purposes:

- **fastapi**: Modern web framework for building APIs
- **uvicorn**: ASGI server for running FastAPI
- **sqlalchemy**: SQL toolkit and ORM
- **psycopg2-binary**: PostgreSQL adapter for Python
- **python-jose**: JWT token creation and verification
- **bcrypt**: Password hashing library
- **pydantic-settings**: Settings management
- **email-validator**: Email validation

## 🤝 Contributing

Suggestions for improvement:

1. Add unit tests (pytest)
2. Add integration tests
3. Add Docker support (Dockerfile, docker-compose.yml)
4. Add CI/CD pipeline (GitHub Actions)
5. Add Redis for token blacklist caching
6. Add metrics and monitoring (Prometheus)
7. Add API rate limiting with Redis
8. Add user roles and permissions

## 📄 License

MIT License - Feel free to use this project for any purpose.

## 📞 Support

For issues, questions, or contributions:
- Check the troubleshooting section above
- Review `CLEANUP_DEPLOYMENT.md` for cleanup-specific issues
- Check application logs for detailed error messages

---

**Made with ❤️ using FastAPI and PostgreSQL**
