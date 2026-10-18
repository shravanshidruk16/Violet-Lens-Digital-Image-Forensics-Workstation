from typing import Dict, Any, List


def generate_forensic_observations(
    integrity_data: Dict[str, Any],
    properties_data: Dict[str, Any],
    signature_data: Dict[str, Any],
    metadata_data: Dict[str, Any],
    ela_data: Dict[str, Any],
    pixel_data: Dict[str, Any]
) -> List[Dict[str, str]]:
    """Synthesize findings across all modules into deterministic, objective forensic observations.
    
    Categorized into:
    - 'info': Factual empirical findings and chain-of-custody milestones.
    - 'review': Anomalies, editing indicators, or inconsistencies requiring human investigator review.
    - 'limitation': Methodological and scientific boundaries of the executed tests.
    """
    observations: List[Dict[str, str]] = []

    # 1. Integrity observations
    sha = integrity_data.get("sha256_hash", "")
    size_fmt = integrity_data.get("byte_size_formatted", "")
    observations.append({
        "category": "info",
        "title": "Cryptographic Hash Fingerprint Established",
        "description": f"SHA-256 digest ({sha[:12]}...{sha[-8:]}) computed directly from {size_fmt} of unaltered original evidence bytes. Establishes baseline chain of custody.",
    })

    # 2. File signature and format consistency
    if signature_data.get("is_consistent"):
        observations.append({
            "category": "info",
            "title": "File Signature & Extension Consistent",
            "description": f"Binary magic bytes match the standard specification for {signature_data.get('detected_signature_format')}, consistent with the '.{signature_data.get('claimed_extension')}' file extension.",
        })
    else:
        observations.append({
            "category": "review",
            "title": "Extension & Header Mismatch Detected",
            "description": f"File extension is '.{signature_data.get('claimed_extension')}', but initial magic bytes identify the stream as {signature_data.get('detected_signature_format')}. May indicate renaming or deliberate extension obfuscation.",
        })

    # 3. Structural Properties
    dims = properties_data.get("dimensions", "")
    mode = properties_data.get("mode", "")
    has_trans = properties_data.get("has_transparency", False)
    observations.append({
        "category": "info",
        "title": "Structural Image Dimensions & Color Mode",
        "description": f"Decoded as {dims} ({properties_data.get('megapixels')} MP), mode '{mode}' with {properties_data.get('channels')} channel(s)." + (" Alpha transparency channel present." if has_trans else ""),
    })

    # 4. EXIF & Metadata
    if metadata_data.get("has_exif"):
        tag_count = metadata_data.get("total_tags_found", 0)
        camera_info = metadata_data.get("camera_device", {})
        make = camera_info.get("make")
        model = camera_info.get("model")
        software = camera_info.get("software")

        dev_desc = f"from {make} {model}" if (make or model) else "without explicit camera make/model"
        observations.append({
            "category": "info",
            "title": "EXIF Metadata Parsed",
            "description": f"Extracted {tag_count} metadata tags {dev_desc}.",
        })

        if camera_info.get("has_editing_software"):
            observations.append({
                "category": "review",
                "title": "Image Processing Software Tag Detected",
                "description": f"EXIF Software field identifies '{software}'. This indicates the image has been processed, edited, or saved through an image manipulation or publishing application.",
            })

        # GPS status
        gps = metadata_data.get("location", {})
        if gps.get("has_gps"):
            observations.append({
                "category": "info",
                "title": "Geolocation Metadata Present",
                "description": "Embedded GPS latitude/longitude coordinates were detected. Coordinates are privacy-masked in accordance with local examination policy.",
            })

        # Timestamp comparison
        ts = metadata_data.get("timestamps", {})
        orig_ts = ts.get("original")
        mod_ts = ts.get("modified")
        if orig_ts and mod_ts and orig_ts != mod_ts:
            observations.append({
                "category": "review",
                "title": "EXIF Timestamp Discrepancy",
                "description": f"Capture date ({orig_ts}) differs from modification date ({mod_ts}). Suggests the file was modified or re-saved at a later time.",
            })
    else:
        observations.append({
            "category": "info",
            "title": "No EXIF Metadata Found",
            "description": "No EXIF metadata segment was found in the byte stream. This is common with images downloaded from social media platforms, messaging applications, or web screenshots, which strip metadata for privacy.",
        })

    # 5. Error Level Analysis (ELA)
    if ela_data.get("is_available"):
        mean_err = ela_data.get("mean_error", 0)
        high_err_pct = ela_data.get("high_error_pixel_percentage", 0)
        observations.append({
            "category": "info",
            "title": "JPEG Error Level Analysis (ELA) Computed",
            "description": f"Resaved at Q={ela_data.get('quality')} with {ela_data.get('scale')}× amplification. Mean recompression error: {mean_err}. High-error pixel density: {high_err_pct}%.",
        })
        if high_err_pct > 25.0:
            observations.append({
                "category": "review",
                "title": "Elevated High-Error Region Density in ELA",
                "description": f"{high_err_pct}% of pixels exhibited significant recompression variance. Inspect the ELA preview for localized brightness differences around suspected edits versus uniform background areas.",
            })
    else:
        observations.append({
            "category": "limitation",
            "title": "Error Level Analysis Not Applicable",
            "description": ela_data.get("reason", "ELA requires a lossy JPEG source."),
        })

    # 6. Radiometric & Pixel Distribution
    summary = pixel_data.get("summary", {})
    shadow_clip = summary.get("shadow_clipping_pct", 0)
    highlight_clip = summary.get("highlight_clipping_pct", 0)
    entropy = summary.get("shannon_entropy_bits", 0)

    if shadow_clip > 15.0 or highlight_clip > 15.0:
        observations.append({
            "category": "review",
            "title": "Dynamic Range Clipping Detected",
            "description": f"Shadow clipping: {shadow_clip}%, Highlight clipping: {highlight_clip}%. Significant pixel values are pegged at extremes (0 or 255), indicating contrast overextension, sensor saturation, or hard clipping.",
        })

    observations.append({
        "category": "info",
        "title": "Pixel Distribution & Entropy Quantified",
        "description": f"Shannon entropy is {entropy:.3f} bits/pixel (max theoretical 8.000 bits). Average luminance is {summary.get('average_luminance', 0):.1f} / 255.",
    })

    # 7. Core Forensic Limitations (Always present for scientific integrity)
    observations.append({
        "category": "limitation",
        "title": "Forensic Evidentiary Boundary",
        "description": "These automated checks provide objective physical and structural indicators. They do not compute a probabilistic 'authenticity score' and must be contextualized by a qualified forensic examiner.",
    })

    return observations
