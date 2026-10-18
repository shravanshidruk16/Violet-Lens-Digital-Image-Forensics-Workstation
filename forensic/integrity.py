import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any


def calculate_sha256(raw_bytes: bytes) -> str:
    """Calculate the deterministic SHA-256 hexadecimal digest of raw bytes.
    
    Must always be calculated directly from the original uploaded byte sequence
    prior to any decoding, transcoding, reorientation, or preprocessing.
    """
    hasher = hashlib.sha256()
    hasher.update(raw_bytes)
    return hasher.hexdigest().lower()


def format_bytes(byte_count: int) -> str:
    """Format byte counts into human-readable strings with binary prefixes."""
    if byte_count < 1024:
        return f"{byte_count} B"
    elif byte_count < 1024 * 1024:
        return f"{byte_count / 1024:.2f} KB"
    elif byte_count < 1024 * 1024 * 1024:
        return f"{byte_count / (1024 * 1024):.2f} MB"
    else:
        return f"{byte_count / (1024 * 1024 * 1024):.2f} GB"


def generate_examination_id() -> str:
    """Generate a cryptographically secure, unpredictable UUIDv4 examination ID."""
    return str(uuid.uuid4())


def get_current_utc_timestamp() -> str:
    """Return the current timestamp in ISO 8601 UTC format."""
    return datetime.now(timezone.utc).isoformat()


def inspect_file_integrity(raw_bytes: bytes, original_filename: str) -> Dict[str, Any]:
    """Generate a comprehensive integrity record for uploaded evidence bytes."""
    byte_size = len(raw_bytes)
    sha256_hash = calculate_sha256(raw_bytes)
    exam_id = generate_examination_id()
    timestamp = get_current_utc_timestamp()

    explanation = (
        "SHA-256 (Secure Hash Algorithm 256-bit) computes a deterministic cryptographic digest "
        "of the exact original byte stream. Any alteration of even a single bit in the file completely "
        "alters this checksum. In digital forensics, cryptographic hashing establishes chain of custody "
        "and bit-level file integrity. Important: A cryptographic hash identifies the specific byte sequence "
        "analyzed; it does not independently prove that an image is genuine, authentic, or unedited prior to capture."
    )

    return {
        "examination_id": exam_id,
        "timestamp_utc": timestamp,
        "original_filename": original_filename,
        "byte_size": byte_size,
        "byte_size_formatted": format_bytes(byte_size),
        "sha256_hash": sha256_hash,
        "hash_algorithm": "SHA-256",
        "integrity_status": "VERIFIED_ORIGINAL_BYTES",
        "forensic_context": explanation,
    }
