import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
from cryptography.fernet import Fernet


class Config:
    # Sécurité
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-moi-en-production")
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

    # Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 Mo max

    ALLOWED_EXTENSIONS = {
        "pdf", "png", "jpg", "jpeg", "gif",
        "txt", "md", "csv", "zip", "docx", "xlsx"
    }

    # Base de données
    DATABASE = os.path.join(BASE_DIR, "openshare.db")