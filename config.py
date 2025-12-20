import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# ------------------------------------
# Database Configuration
# ------------------------------------
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL","mysql+pymysql://root:JSPCikIqwwbeYgBzbdvWGrMvCAGdwHvj@caboose.proxy.rlwy.net:40426/railway")

# ------------------------------------
# Security Configuration (JWT)
# ------------------------------------
SECRET_KEY = os.environ.get("JWT_SECRET", "171a64956fbdf8c2f8e6af81fd8edf3012aa6ba9414d51c440d55bbc8932f1a2")
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

# ------------------------------------
# Communication Service URL
# ------------------------------------
MAIL_SERVICE_URL = os.environ.get("MAIL_SERVICE_URL", "https://mail-service-flax.vercel.app")
