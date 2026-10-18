import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 Megabytes upload ceiling
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif"}
    MAX_IMAGE_PIXELS = 50_000_000  # Pillow decompression bomb guard (50 Megapixels)
    
    # Secure isolated temporary storage for active examinations
    EXAMINATIONS_DIR = BASE_DIR / "instance" / "examinations"
    EXAMINATION_TTL_SECONDS = 3600  # 1 hour expiration for temporary artifacts
    
    # ELA Analysis defaults
    ELA_JPEG_QUALITY = 90
    ELA_SCALE_FACTOR = 15
    
    # Server configuration
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("FLASK_DEBUG", "0").strip() in {"1", "true", "True"}
