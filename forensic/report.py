import html
from typing import Dict, Any, List


def generate_examination_report(
    integrity: Dict[str, Any],
    properties: Dict[str, Any],
    signature: Dict[str, Any],
    metadata: Dict[str, Any],
    ela: Dict[str, Any],
    pixels: Dict[str, Any],
    observations: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Assemble a comprehensive, JSON-serializable digital forensic examination report."""
    
    # Clean and sanitize filename for safe display
    safe_filename = html.escape(integrity.get("original_filename", "unnamed_evidence"))

    # Sanitize metadata tags to prevent payload injection into downstream consumers
    sanitized_metadata = {}
    for tag_name, tag_val in metadata.get("all_tags", {}).items():
        if isinstance(tag_val, str):
            sanitized_metadata[tag_name] = html.escape(tag_val)
        else:
            sanitized_metadata[tag_name] = tag_val

    # Strip large base64 image strings from the exported JSON report payload
    ela_report_summary = {
        "is_available": ela.get("is_available", False),
        "quality": ela.get("quality"),
        "scale_factor": ela.get("scale"),
        "mean_error": ela.get("mean_error"),
        "max_error": ela.get("max_error"),
        "std_error": ela.get("std_error"),
        "high_error_pixel_percentage": ela.get("high_error_pixel_percentage"),
        "scientific_note": ela.get("scientific_note"),
        "reason_if_unavailable": ela.get("reason"),
    }

    report = {
        "$schema": "https://violetlens.local/schemas/forensic-report-v1.json",
        "workstation": {
            "name": "Violet Lens — Digital Image Forensics Workstation",
            "version": "1.0.0",
            "course": "Computer Engineering CSDF Mini-Project",
            "syllabus_title": "Design and develop a tool for digital forensic of images",
            "execution_environment": "Local Offline Workstation",
        },
        "examination": {
            "id": integrity.get("examination_id"),
            "timestamp_utc": integrity.get("timestamp_utc"),
            "status": "COMPLETED",
        },
        "evidence_integrity": {
            "filename": safe_filename,
            "byte_size": integrity.get("byte_size"),
            "byte_size_formatted": integrity.get("byte_size_formatted"),
            "hash_algorithm": integrity.get("hash_algorithm"),
            "sha256": integrity.get("sha256_hash"),
            "integrity_context": integrity.get("forensic_context"),
        },
        "file_signature": {
            "claimed_extension": signature.get("claimed_extension"),
            "detected_signature": signature.get("detected_signature_format"),
            "signature_description": signature.get("signature_description"),
            "magic_bytes_hex": signature.get("magic_bytes_hex"),
            "is_consistent": signature.get("is_consistent"),
            "details": signature.get("details"),
        },
        "image_properties": {
            "dimensions": properties.get("dimensions"),
            "width_px": properties.get("width"),
            "height_px": properties.get("height"),
            "megapixels": properties.get("megapixels"),
            "aspect_ratio": properties.get("aspect_ratio"),
            "detected_format": properties.get("format"),
            "color_mode": properties.get("mode"),
            "channel_count": properties.get("channels"),
            "has_transparency": properties.get("has_transparency"),
            "frame_count": properties.get("frame_count"),
        },
        "metadata_inspection": {
            "has_exif": metadata.get("has_exif"),
            "total_tags_found": metadata.get("total_tags_found"),
            "camera_device": metadata.get("camera_device"),
            "timestamps": metadata.get("timestamps"),
            "optical_settings": metadata.get("optical_settings"),
            "location_summary": {
                "has_gps": metadata.get("location", {}).get("has_gps", False),
                "coordinates_detected": metadata.get("location", {}).get("has_coordinates", False),
                "coordinates_masked_status": metadata.get("location", {}).get("status_description"),
                "coordinates_formatted": metadata.get("location", {}).get("coordinates_formatted"),
                "latitude_decimal": metadata.get("location", {}).get("latitude_decimal"),
                "longitude_decimal": metadata.get("location", {}).get("longitude_decimal"),
                "altitude": metadata.get("location", {}).get("altitude"),
            },
            "all_tags": sanitized_metadata,
            "forensic_note": metadata.get("forensic_note"),
        },
        "error_level_analysis": ela_report_summary,
        "pixel_and_color_analysis": {
            "summary": pixels.get("summary"),
            "channel_statistics": pixels.get("channel_statistics"),
            "forensic_context": pixels.get("forensic_context"),
        },
        "observations": observations,
        "methodology_and_limitations": [
            "SHA-256 uniquely identifies the submitted byte sequence; it cannot verify pre-acquisition chain of custody.",
            "EXIF metadata is user-space data that can be injected, wiped, or modified without altering image pixels.",
            "Absence of EXIF does not indicate tampering; social networks routinely strip metadata upon upload.",
            "Error Level Analysis is an empirical heuristic for JPEG recompression variance and does not establish algorithmic proof of forgery.",
            "Histogram statistics quantify distribution anomalies and clipping but do not pinpoint local compositing boundaries.",
            "All findings are forensic indicators that must be corroborated by a certified digital forensics investigator.",
        ],
    }

    return report
