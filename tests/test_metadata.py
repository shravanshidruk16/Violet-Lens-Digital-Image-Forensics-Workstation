import io
import json
from PIL import Image
from forensic.metadata import extract_metadata


def test_metadata_extraction_with_exif(sample_jpeg_with_exif_bytes):
    """Test parsing of Make, Model, Software, and GPS from synthetic EXIF image."""
    img = Image.open(io.BytesIO(sample_jpeg_with_exif_bytes))
    meta = extract_metadata(img, sample_jpeg_with_exif_bytes)

    assert meta["has_exif"] is True
    assert meta["total_tags_found"] > 0
    assert meta["camera_device"]["make"] == "ForensicTestCam"
    assert meta["camera_device"]["model"] == "Model-X100"
    assert "Photoshop" in meta["camera_device"]["software"]
    assert meta["camera_device"]["has_editing_software"] is True

    # GPS presence
    gps = meta["location"]
    assert gps["has_gps"] is True
    assert gps["has_coordinates"] is True
    assert abs(gps["latitude_decimal"] - 40.7128) < 0.05
    assert abs(gps["longitude_decimal"] - (-74.0058)) < 0.05

    # JSON serialization safety
    json_str = json.dumps(meta)
    assert len(json_str) > 0


def test_metadata_extraction_without_exif(sample_png_bytes):
    """Test that an image with no EXIF returns structured False without errors."""
    img = Image.open(io.BytesIO(sample_png_bytes))
    meta = extract_metadata(img, sample_png_bytes)

    assert meta["has_exif"] is False
    assert meta["total_tags_found"] == 0
    assert meta["camera_device"]["make"] is None
    assert meta["location"]["has_gps"] is False


def test_corrupt_exif_does_not_crash(sample_jpeg_bytes):
    """Ensure malformed EXIF payload does not trigger an uncaught exception."""
    img = Image.open(io.BytesIO(sample_jpeg_bytes))
    # Inject junk raw bytes
    meta = extract_metadata(img, b"\xFF\xD8\xFF\xE1" + b"\x00\x00" + b"\xDE\xAD\xBE\xEF")
    assert isinstance(meta, dict)
    assert "has_exif" in meta
