import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

FRONTEND_FOLDER = os.path.join(PROJECT_ROOT, "frontend")
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")

MAX_UPLOAD_SIZE = 100 * 1024 * 1024
DEFAULT_MESSAGE_FETCH_LIMIT = 50
TOKEN_MAX_AGE_DAYS = 30