import os
from typing import Dict, Any, Optional

# Magic byte signatures for supported forensic image formats
KNOWN_SIGNATURES = [
    {
        "format": "JPEG",
        "description": "JPEG / JFIF / EXIF Image",
        "matches": lambda b: len(b) >= 3 and b[:3] == b"\xFF\xD8\xFF",
        "extensions": {"jpg", "jpeg", "jpe", "jfif"},
    },
    {
        "format": "PNG",
        "description": "Portable Network Graphics",
        "matches": lambda b: len(b) >= 8 and b[:8] == b"\x89PNG\r\n\x1a\n",
        "extensions": {"png"},
    },
    {
        "format": "WEBP",
        "description": "Google WebP (RIFF container)",
        "matches": lambda b: len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WEBP",
        "extensions": {"webp"},
    },
    {
        "format": "TIFF",
        "description": "Tagged Image File Format (Little-Endian Intel)",
        "matches": lambda b: len(b) >= 4 and b[:4] == b"II*\x00",
        "extensions": {"tif", "tiff"},
    },
    {
        "format": "TIFF",
        "description": "Tagged Image File Format (Big-Endian Motorola)",
        "matches": lambda b: len(b) >= 4 and b[:4] == b"MM\x00*",
        "extensions": {"tif", "tiff"},
    },
    {
        "format": "BMP",
        "description": "Windows Bitmap",
        "matches": lambda b: len(b) >= 2 and b[:2] == b"BM",
        "extensions": {"bmp"},
    },
    {
        "format": "GIF",
        "description": "Graphics Interchange Format",
        "matches": lambda b: len(b) >= 6 and (b[:6] == b"GIF87a" or b[:6] == b"GIF89a"),
        "extensions": {"gif"},
    },
]


def detect_file_signature(raw_bytes: bytes) -> Optional[Dict[str, Any]]:
    """Inspect raw header bytes and return matching signature definition."""
    for sig in KNOWN_SIGNATURES:
        if sig["matches"](raw_bytes):
            return sig
    return None


def get_first_bytes_hex(raw_bytes: bytes, count: int = 16) -> str:
    """Return formatted hexadecimal string of initial header bytes."""
    header = raw_bytes[:count]
    return " ".join(f"{b:02X}" for b in header)


def check_format_consistency(
    raw_bytes: bytes,
    original_filename: str,
    pillow_format: Optional[str] = None
) -> Dict[str, Any]:
    """Verify consistency between file extension, magic byte signature, and Pillow decoding.
    
    A discrepancy between extension and content is a recognized forensic indicator.
    It may result from benign renaming or deliberate extension spoofing.
    """
    ext = os.path.splitext(original_filename)[1].lstrip(".").lower()
    sig = detect_file_signature(raw_bytes)
    header_hex = get_first_bytes_hex(raw_bytes, 16)
    
    if sig:
        detected_sig_format = sig["format"]
        sig_description = sig["description"]
        expected_extensions = sig["extensions"]
        is_consistent = ext in expected_extensions
        
        if is_consistent:
            status = "CONSISTENT"
            details = (
                f"The initial file bytes ({header_hex[:11]}...) match the standard {detected_sig_format} "
                f"specification, which corresponds to the claimed '.{ext}' extension."
            )
        else:
            status = "MISMATCH_DETECTED"
            details = (
                f"Discrepancy detected: The file extension is '.{ext}', but binary magic bytes identify "
                f"the content as {detected_sig_format} ({sig_description}). While this may occur during accidental "
                f"renaming, it is an important forensic indicator that warrants investigative verification."
            )
    else:
        detected_sig_format = "UNKNOWN"
        sig_description = "Unrecognized binary header"
        expected_extensions = set()
        is_consistent = False
        status = "UNKNOWN_SIGNATURE"
        details = (
            f"The initial header bytes ({header_hex}) do not match standard recognized forensic image signatures."
        )

    # Cross-reference with Pillow's detected format if provided
    pillow_consistent = True
    if pillow_format and detected_sig_format != "UNKNOWN":
        norm_pillow = pillow_format.upper()
        if norm_pillow == "JPEG":
            pillow_consistent = detected_sig_format == "JPEG"
        elif norm_pillow == "PNG":
            pillow_consistent = detected_sig_format == "PNG"
        elif norm_pillow == "WEBP":
            pillow_consistent = detected_sig_format == "WEBP"
        elif norm_pillow == "BMP":
            pillow_consistent = detected_sig_format == "BMP"
        elif norm_pillow == "TIFF":
            pillow_consistent = detected_sig_format == "TIFF"

    return {
        "claimed_extension": ext,
        "magic_bytes_hex": header_hex,
        "detected_signature_format": detected_sig_format,
        "signature_description": sig_description,
        "is_consistent": is_consistent,
        "pillow_format": pillow_format,
        "pillow_consistent": pillow_consistent,
        "status": status,
        "details": details,
    }
