import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# ------------------------------------
# Database Configuration
# ------------------------------------
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    # Fallback only for totally local dev if .env is missing, but preferably warn
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" 

# ------------------------------------
# Security Configuration (JWT)
# ------------------------------------
SECRET_KEY = os.environ.get("JWT_SECRET", "default-insecure-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ACCESS_TOKEN_EXPIRE_DELTA = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

# ------------------------------------
# System Roles
# ------------------------------------
ROLES = ["Admin", "Seating Manager", "Club Coordinator", "Student"]

# ------------------------------------
# Root URL for OAuth2 (for Swagger documentation)
# ------------------------------------
TOKEN_URL = "/api/auth/token"