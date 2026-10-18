import base64
import io
import math
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageOps, UnidentifiedImageError

# Restrict maximum pixel count to prevent decompression bomb attacks
MAX_IMAGE_PIXELS = 50_000_000
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "TIFF", "GIF"}


def compute_aspect_ratio(width: int, height: int) -> str:
    """Compute simplified aspect ratio string or standard decimal representation."""
    if width <= 0 or height <= 0:
        return "Unknown"
    divisor = math.gcd(width, height)
    simplified_w = width // divisor
    simplified_h = height // divisor
    # If ratio is clean integer ratio under 50:50, return fraction
    if simplified_w <= 32 and simplified_h <= 32:
        return f"{simplified_w}:{simplified_h} ({width / height:.2f}:1)"
    return f"{width / height:.2f}:1"


def get_channel_count(mode: str) -> int:
    """Return number of color/alpha channels associated with Pillow mode."""
    mode_channels = {
        "1": 1,
        "L": 1,
        "P": 1,
        "RGB": 3,
        "RGBA": 4,
        "CMYK": 4,
        "YCbCr": 3,
        "LAB": 3,
        "HSV": 3,
        "I": 1,
        "F": 1,
        "LA": 2,
        "RGBa": 4,
    }
    return mode_channels.get(mode, len(mode))


def detect_transparency(img: Image.Image) -> bool:
    """Check if the image possesses transparency channels or palette transparency."""
    if img.mode in ("RGBA", "LA", "RGBa"):
        return True
    if "transparency" in img.info:
        return True
    return False


def load_and_inspect_image(raw_bytes: bytes) -> Tuple[Image.Image, Dict[str, Any]]:
    """Safely validate, open, and inspect image properties from raw evidence bytes.
    
    Returns the opened PIL Image instance alongside a detailed properties dictionary.
    Raises ValueError or UnidentifiedImageError on malformed or unsupported content.
    """
    if not raw_bytes or len(raw_bytes) == 0:
        raise ValueError("Upload payload is empty (zero bytes received).")

    # Guard against decompression bomb before loading
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    # First verify image integrity using a dedicated verification pass
    try:
        verify_stream = io.BytesIO(raw_bytes)
        with Image.open(verify_stream) as test_img:
            test_img.verify()
    except Exception as e:
        raise ValueError(f"Corrupt or malformed image data: {str(e)}")

    # Open fresh instance for property inspection and reading
    stream = io.BytesIO(raw_bytes)
    try:
        img = Image.open(stream)
    except UnidentifiedImageError:
        raise ValueError("File content is not a recognized digital image format.")
    except Exception as e:
        raise ValueError(f"Unable to decode image: {str(e)}")

    detected_format = (img.format or "UNKNOWN").upper()
    width, height = img.size
    mode = img.mode
    aspect_ratio = compute_aspect_ratio(width, height)
    channels = get_channel_count(mode)
    has_transparency = detect_transparency(img)
    megapixels = round((width * height) / 1_000_000, 2)
    frame_count = getattr(img, "n_frames", 1)

    # Detect EXIF orientation tag if present
    orientation_val = None
    try:
        exif_data = img.getexif()
        if exif_data and 274 in exif_data:
            orientation_val = int(exif_data[274])
    except Exception:
        pass

    properties = {
        "width": width,
        "height": height,
        "dimensions": f"{width} × {height}",
        "megapixels": megapixels,
        "aspect_ratio": aspect_ratio,
        "format": detected_format,
        "mode": mode,
        "channels": channels,
        "has_transparency": has_transparency,
        "frame_count": frame_count,
        "raw_orientation_tag": orientation_val,
        "is_animated": frame_count > 1,
    }

    return img, properties


def generate_display_preview(img: Image.Image, max_dim: int = 1600) -> str:
    """Generate an optimized base64 data URI of the image for safe browser display.
    
    Crucial: This generates a display representation only and never alters
    the raw uploaded byte sequence.
    """
    preview = img.copy()
    
    # Check orientation and apply preview rotation if appropriate
    try:
        preview = ImageOps.exif_transpose(preview)
    except Exception:
        pass

    # Downscale if excessively large to avoid browser memory pressure
    if preview.width > max_dim or preview.height > max_dim:
        preview.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    # Format into appropriate display format
    output_io = io.BytesIO()
    if preview.mode in ("RGBA", "LA") or (preview.mode == "P" and "transparency" in preview.info):
        preview.save(output_io, format="PNG", optimize=True)
        mime = "image/png"
    else:
        if preview.mode != "RGB":
            preview = preview.convert("RGB")
        preview.save(output_io, format="JPEG", quality=85, optimize=True)
        mime = "image/jpeg"

    output_bytes = output_io.getvalue()
    b64_str = base64.b64encode(output_bytes).decode("ascii")
    return f"data:{mime};base64,{b64_str}"
