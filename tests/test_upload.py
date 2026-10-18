import io
import pytest


def test_valid_jpeg_upload(client, sample_jpeg_bytes):
    """Ensure valid JPEG upload succeeds with 200 and complete structure."""
    data = {
        "image": (io.BytesIO(sample_jpeg_bytes), "evidence.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert "examination_id" in json_data
    assert json_data["properties"]["format"] == "JPEG"
    assert json_data["signature"]["is_consistent"] is True


def test_valid_png_upload(client, sample_png_bytes):
    """Ensure valid PNG upload with alpha transparency succeeds."""
    data = {
        "image": (io.BytesIO(sample_png_bytes), "sample.png")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["properties"]["format"] == "PNG"
    assert json_data["properties"]["has_transparency"] is True
    assert json_data["signature"]["is_consistent"] is True


def test_valid_webp_upload(client, sample_webp_bytes):
    """Ensure valid WebP upload succeeds."""
    data = {
        "image": (io.BytesIO(sample_webp_bytes), "photo.webp")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["properties"]["format"] == "WEBP"


def test_valid_bmp_upload(client, sample_bmp_bytes):
    """Ensure valid BMP upload succeeds."""
    data = {
        "image": (io.BytesIO(sample_bmp_bytes), "chart.bmp")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["properties"]["format"] == "BMP"


def test_empty_upload_payload(client):
    """Ensure empty file (0 bytes) is rejected with 400 error."""
    data = {
        "image": (io.BytesIO(b""), "empty.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    json_data = res.get_json()
    assert "empty" in json_data["error"].lower()


def test_missing_image_field(client):
    """Ensure request lacking the 'image' field is rejected with 400."""
    res = client.post("/api/analyze", data={}, content_type="multipart/form-data")
    assert res.status_code == 400
    json_data = res.get_json()
    assert "no image payload" in json_data["error"].lower()


def test_invalid_disguised_bytes(client):
    """Ensure arbitrary non-image text bytes disguised as .jpg are rejected."""
    corrupt_bytes = b"This is not a real JPEG image file at all. It is pure text."
    data = {
        "image": (io.BytesIO(corrupt_bytes), "fake_photo.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 400
    json_data = res.get_json()
    assert "validation failed" in json_data["error"].lower()


def test_extension_content_mismatch_detected(client, sample_png_bytes):
    """Ensure a PNG file renamed to .jpg is flagged as an extension mismatch."""
    data = {
        "image": (io.BytesIO(sample_png_bytes), "disguised_png.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["signature"]["is_consistent"] is False
    assert json_data["signature"]["status"] == "MISMATCH_DETECTED"
    assert json_data["signature"]["detected_signature_format"] == "PNG"
    assert json_data["signature"]["claimed_extension"] == "jpg"
