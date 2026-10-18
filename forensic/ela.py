import base64
import io
from typing import Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image


def perform_error_level_analysis(
    img: Image.Image,
    detected_format: str,
    jpeg_quality: int = 90,
    scale_factor: int = 15
) -> Dict[str, Any]:
    """Perform deterministic Error Level Analysis (ELA) on JPEG images.
    
    ELA resaves the image at a known JPEG compression quality (default 90)
    and computes the amplified absolute difference between original and resaved pixels.
    Different compression histories across regions create differing error levels.
    """
    norm_format = (detected_format or "").upper()
    if norm_format not in ("JPEG", "JPG"):
        return {
            "is_available": False,
            "reason": (
                f"Error Level Analysis is designed specifically for lossy JPEG 8x8 Discrete Cosine "
                f"Transform (DCT) compression grids. The uploaded evidence is in '{norm_format}' format, "
                f"which uses lossless or non-JPEG encoding. Standard JPEG ELA cannot be reliably applied."
            ),
            "quality": None,
            "scale": None,
            "mean_error": None,
            "max_error": None,
            "std_error": None,
            "preview_data_uri": None,
            "scientific_note": "ELA is intentionally restricted to genuine JPEG sources to avoid misleading forensic artifacts.",
        }

    try:
        # Convert original image to RGB mode for consistent comparison
        orig_rgb = img.convert("RGB")
        orig_arr = np.asarray(orig_rgb, dtype=np.float32)

        # Recompress image into an in-memory JPEG stream at specified quality
        recompressed_io = io.BytesIO()
        orig_rgb.save(recompressed_io, format="JPEG", quality=jpeg_quality)
        recompressed_io.seek(0)
        
        # Load recompressed JPEG
        recomp_img = Image.open(recompressed_io).convert("RGB")
        recomp_arr = np.asarray(recomp_img, dtype=np.float32)

        # Compute absolute difference
        abs_diff = np.abs(orig_arr - recomp_arr)
        
        # Compute real forensic metrics before visual amplification
        mean_error = float(np.mean(abs_diff))
        max_error = float(np.max(abs_diff))
        std_error = float(np.std(abs_diff))
        
        # Percentage of pixels with error > 10 levels
        high_error_ratio = float(np.mean(abs_diff > 10.0) * 100.0)

        # Amplify differences by scale factor and clip into 8-bit unsigned integer range
        amplified = np.clip(abs_diff * scale_factor, 0, 255).astype(np.uint8)
        ela_img = Image.fromarray(amplified)


        # Encode ELA visualization as a lossless PNG data URI for client rendering
        out_stream = io.BytesIO()
        ela_img.save(out_stream, format="PNG", optimize=True)
        ela_bytes = out_stream.getvalue()
        b64_str = base64.b64encode(ela_bytes).decode("ascii")
        preview_data_uri = f"data:image/png;base64,{b64_str}"

        return {
            "is_available": True,
            "quality": jpeg_quality,
            "scale": scale_factor,
            "mean_error": round(mean_error, 3),
            "max_error": round(max_error, 2),
            "std_error": round(std_error, 3),
            "high_error_pixel_percentage": round(high_error_ratio, 2),
            "preview_data_uri": preview_data_uri,
            "raw_png_bytes": ela_bytes,
            "scientific_note": (
                f"ELA generated with JPEG recompression quality {jpeg_quality} and {scale_factor}× amplification. "
                "Interpretation guide: Uniform error levels across similar textures generally indicate a shared compression history. "
                "Significant localized variations in error level—especially around edges, spliced objects, or pasted text—may "
                "indicate that those regions were saved under different compression parameters. However, natural high-contrast "
                "edges and high-frequency textures inherently produce elevated error levels; ELA is an investigative heuristic "
                "and does not constitute definitive proof of digital manipulation."
            ),
        }
    except Exception as e:
        return {
            "is_available": False,
            "reason": f"ELA calculation encountered an error: {str(e)}",
            "quality": None,
            "scale": None,
            "mean_error": None,
            "max_error": None,
            "std_error": None,
            "preview_data_uri": None,
            "scientific_note": "ELA execution failed safely without interrupting other forensic analysis steps.",
        }
