import hashlib
import io
from forensic.integrity import calculate_sha256, inspect_file_integrity


def test_sha256_exact_hash_match(sample_jpeg_bytes):
    """Verify calculate_sha256 matches standard hashlib output bit-for-bit."""
    expected_hash = hashlib.sha256(sample_jpeg_bytes).hexdigest().lower()
    computed_hash = calculate_sha256(sample_jpeg_bytes)
    assert computed_hash == expected_hash
    assert len(computed_hash) == 64


def test_integrity_module_structure(sample_png_bytes):
    """Verify integrity record contains all required chain-of-custody fields."""
    rec = inspect_file_integrity(sample_png_bytes, "test_evidence.png")
    assert rec["sha256_hash"] == hashlib.sha256(sample_png_bytes).hexdigest().lower()
    assert rec["byte_size"] == len(sample_png_bytes)
    assert rec["original_filename"] == "test_evidence.png"
    assert rec["hash_algorithm"] == "SHA-256"
    assert "examination_id" in rec
    assert "timestamp_utc" in rec


def test_api_integrity_preservation(client, sample_jpeg_bytes):
    """Ensure the API report's SHA-256 matches hashlib applied to the original bytes."""
    data = {
        "image": (io.BytesIO(sample_jpeg_bytes), "original_evidence.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()

    expected_hash = hashlib.sha256(sample_jpeg_bytes).hexdigest().lower()
    assert json_data["integrity"]["sha256_hash"] == expected_hash
