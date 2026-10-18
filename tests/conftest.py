import io
import shutil
import tempfile
from pathlib import Path
import pytest
from PIL import Image
import piexif

from app import create_app
from config import Config


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    # Use temporary folder for examinations during test runs
    EXAMINATIONS_DIR = Path(tempfile.mkdtemp(prefix="test_examinations_"))
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024


@pytest.fixture(scope="session")
def app():
    """Create configured Flask application instance for automated testing."""
    test_app = create_app(TestConfig)
    yield test_app
    # Teardown temporary directory
    shutil.rmtree(TestConfig.EXAMINATIONS_DIR, ignore_errors=True)


@pytest.fixture
def client(app):
    """Provide Flask test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def sample_jpeg_bytes():
    """Generate in-memory valid JPEG image bytes."""
    img = Image.new("RGB", (120, 100), color=(116, 80, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


@pytest.fixture
def sample_png_bytes():
    """Generate in-memory valid PNG image bytes with alpha transparency."""
    img = Image.new("RGBA", (80, 80), color=(231, 106, 168, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_webp_bytes():
    """Generate in-memory valid WebP image bytes."""
    img = Image.new("RGB", (64, 64), color=(40, 21, 47))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture
def sample_bmp_bytes():
    """Generate in-memory valid BMP image bytes."""
    img = Image.new("RGB", (50, 50), color=(242, 236, 249))
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    return buf.getvalue()


@pytest.fixture
def sample_jpeg_with_exif_bytes():
    """Generate in-memory JPEG containing test EXIF metadata (Make, Model, Software, GPS)."""
    img = Image.new("RGB", (100, 100), color=(81, 53, 142))
    
    # Construct synthetic EXIF payload using piexif
    zeroth_ifd = {
        piexif.ImageIFD.Make: "ForensicTestCam",
        piexif.ImageIFD.Model: "Model-X100",
        piexif.ImageIFD.Software: "Adobe Photoshop 24.1",
        piexif.ImageIFD.DateTime: "2026:03:15 10:30:00",
    }
    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: "2026:03:14 14:22:10",
        piexif.ExifIFD.DateTimeDigitized: "2026:03:14 14:22:10",
        piexif.ExifIFD.FNumber: (28, 10),  # f/2.8
        piexif.ExifIFD.ExposureTime: (1, 250),  # 1/250s
        piexif.ExifIFD.ISOSpeedRatings: 400,
        piexif.ExifIFD.FocalLength: (500, 10),  # 50mm
    }
    # GPS: 40 deg 42 min 46 sec N, 74 deg 0 min 21 sec W
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: "N",
        piexif.GPSIFD.GPSLatitude: ((40, 1), (42, 1), (4600, 100)),
        piexif.GPSIFD.GPSLongitudeRef: "W",
        piexif.GPSIFD.GPSLongitude: ((74, 1), (0, 1), (2100, 100)),
        piexif.GPSIFD.GPSAltitude: (150, 1),
    }
    
    exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd, "1st": {}, "thumbnail": None}
    exif_bytes = piexif.dump(exif_dict)
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif_bytes)
    return buf.getvalue()
