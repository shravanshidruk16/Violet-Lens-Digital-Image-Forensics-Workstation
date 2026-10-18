import io
import hashlib
from PIL import Image
from forensic.ela import perform_error_level_analysis


def test_valid_jpeg_ela_generation(sample_jpeg_bytes):
    """Ensure valid JPEG generates deterministic ELA metrics and PNG preview."""
    original_hash = hashlib.sha256(sample_jpeg_bytes).hexdigest()
    img = Image.open(io.BytesIO(sample_jpeg_bytes))
    
    ela = perform_error_level_analysis(img, "JPEG", jpeg_quality=90, scale_factor=15)
    
    assert ela["is_available"] is True
    assert ela["quality"] == 90
    assert ela["scale"] == 15
    assert isinstance(ela["mean_error"], float)
    assert isinstance(ela["max_error"], float)
    assert isinstance(ela["std_error"], float)
    assert "data:image/png;base64," in ela["preview_data_uri"]
    
    # Verify original bytes remain unmodified
    post_hash = hashlib.sha256(sample_jpeg_bytes).hexdigest()
    assert original_hash == post_hash


def test_non_jpeg_ela_marked_unavailable(sample_png_bytes):
    """Ensure PNG file returns is_available: False with honest technical explanation."""
    img = Image.open(io.BytesIO(sample_png_bytes))
    ela = perform_error_level_analysis(img, "PNG")
    
    assert ela["is_available"] is False
    assert "PNG" in ela["reason"]
    assert ela["preview_data_uri"] is None


def test_ela_error_resilience():
    """Ensure unexpected exception handling in ELA fails gracefully without breaking."""
    # Pass a dummy object that will fail when converted
    class BrokenImage:
        def convert(self, mode):
            raise RuntimeError("Synthetic simulated decoder failure")
            
    ela = perform_error_level_analysis(BrokenImage(), "JPEG")
    assert ela["is_available"] is False
    assert "error" in ela["reason"].lower()
