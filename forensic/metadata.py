from typing import Dict, Any, Optional, Tuple, List
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif


def _safe_convert_value(val: Any) -> Any:
    """Recursively convert EXIF values, rationals, bytes, and tuples into JSON-serializable types."""
    if val is None:
        return None
    if isinstance(val, (int, float, bool, str)):
        return val
    if isinstance(val, bytes):
        try:
            cleaned = val.decode("utf-8").strip("\x00 \r\n\t")
            if cleaned.isprintable():
                return cleaned
        except Exception:
            pass
        # Return truncated hex representation for binary payloads
        hex_rep = val[:32].hex()
        return f"[Binary data: {len(val)} bytes, hex: {hex_rep}...]"
    if isinstance(val, (list, tuple)):
        # Check if it represents a rational number: (numerator, denominator)
        if len(val) == 2 and isinstance(val[0], int) and isinstance(val[1], int) and val[1] != 0:
            if val[1] == 1:
                return val[0]
            # Avoid repeating floats like 1/3
            val_float = round(val[0] / val[1], 4)
            return val_float
        return [_safe_convert_value(x) for x in val]
    if isinstance(val, dict):
        return {str(k): _safe_convert_value(v) for k, v in val.items()}
    # Pillow IFDRational or custom object
    if hasattr(val, "numerator") and hasattr(val, "denominator"):
        denom = getattr(val, "denominator", 1)
        num = getattr(val, "numerator", 0)
        if denom == 0:
            return 0
        if denom == 1:
            return num
        return round(float(num) / float(denom), 4)
    return str(val)


def _dms_to_decimal(dms_tuple: Any, ref: str) -> Optional[float]:
    """Convert EXIF GPS Degrees, Minutes, Seconds rational tuple into decimal degrees."""
    try:
        if not dms_tuple or len(dms_tuple) != 3:
            return None
        d = float(_safe_convert_value(dms_tuple[0]))
        m = float(_safe_convert_value(dms_tuple[1]))
        s = float(_safe_convert_value(dms_tuple[2]))
        decimal = d + (m / 60.0) + (s / 3600.0)
        if ref in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except Exception:
        return None


def extract_gps_data(gps_ifd: Dict[int, Any]) -> Dict[str, Any]:
    """Extract and parse GPS metadata with sensitive disclosure controls."""
    if not gps_ifd:
        return {
            "has_gps": False,
            "status_description": "No GPS geolocation metadata present in image.",
        }

    # Resolve GPS tag names
    gps_named: Dict[str, Any] = {}
    for tag_id, val in gps_ifd.items():
        tag_name = GPSTAGS.get(tag_id, str(tag_id))
        gps_named[tag_name] = _safe_convert_value(val)

    lat_dms = gps_ifd.get(2)  # GPSLatitude
    lat_ref = gps_ifd.get(1, "N")  # GPSLatitudeRef
    if isinstance(lat_ref, bytes):
        lat_ref = lat_ref.decode("ascii", errors="ignore").strip()

    lon_dms = gps_ifd.get(4)  # GPSLongitude
    lon_ref = gps_ifd.get(3, "E")  # GPSLongitudeRef
    if isinstance(lon_ref, bytes):
        lon_ref = lon_ref.decode("ascii", errors="ignore").strip()

    alt_val = gps_ifd.get(6)  # GPSAltitude
    alt_ref = gps_ifd.get(5, 0)  # 0 = above sea level, 1 = below sea level

    lat_dec = _dms_to_decimal(lat_dms, str(lat_ref))
    lon_dec = _dms_to_decimal(lon_dms, str(lon_ref))

    altitude = None
    if alt_val is not None:
        try:
            alt_float = float(_safe_convert_value(alt_val))
            if alt_ref == 1:
                alt_float = -alt_float
            altitude = f"{round(alt_float, 1)} m"
        except Exception:
            pass

    has_coordinates = (lat_dec is not None and lon_dec is not None)

    return {
        "has_gps": True,
        "has_coordinates": has_coordinates,
        "latitude_decimal": lat_dec,
        "longitude_decimal": lon_dec,
        "latitude_ref": lat_ref,
        "longitude_ref": lon_ref,
        "altitude": altitude,
        "coordinates_formatted": f"{lat_dec:.5f}° {lat_ref}, {lon_dec:.5f}° {lon_ref}" if has_coordinates else None,
        "status_description": (
            "GPS location metadata is present. Coordinates are privacy-shielded by default "
            "and can be inspected locally on demand."
        ),
        "raw_gps_tags": gps_named,
    }


def extract_metadata(img: Image.Image, raw_bytes: bytes) -> Dict[str, Any]:
    """Perform comprehensive, fault-tolerant EXIF and structural metadata inspection.
    
    Inspects camera hardware, editing software, timestamps, optical parameters,
    and GPS coordinates. Returns structured JSON-safe groups.
    """
    raw_exif_dict: Dict[int, Any] = {}
    gps_ifd: Dict[int, Any] = {}
    
    # 1. Attempt extraction via Pillow getexif()
    try:
        exif_obj = img.getexif()
        if exif_obj:
            for k, v in exif_obj.items():
                raw_exif_dict[k] = v
            # GPS IFD is tag 34853 (0x8825)
            if 34853 in raw_exif_dict:
                try:
                    gps_ifd_data = exif_obj.get_ifd(34853)
                    for gk, gv in gps_ifd_data.items():
                        gps_ifd[gk] = gv
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Attempt legacy _getexif() for deeper EXIF tag support
    try:
        if hasattr(img, "_getexif"):
            legacy_exif = img._getexif()
            if legacy_exif:
                for k, v in legacy_exif.items():
                    if k not in raw_exif_dict:
                        raw_exif_dict[k] = v
                    if k == 34853 and isinstance(v, dict):
                        for gk, gv in v.items():
                            gps_ifd[gk] = gv
    except Exception:
        pass

    # 3. If JPEG or TIFF, try piexif fallback for missing tags
    if not raw_exif_dict and img.format in ("JPEG", "TIFF"):
        try:
            exif_dict = piexif.load(raw_bytes)
            for ifd_name in ("0th", "Exif", "1st"):
                if ifd_name in exif_dict and isinstance(exif_dict[ifd_name], dict):
                    for tag_id, val in exif_dict[ifd_name].items():
                        raw_exif_dict[tag_id] = val
            if "GPS" in exif_dict and isinstance(exif_dict["GPS"], dict):
                for tag_id, val in exif_dict["GPS"].items():
                    gps_ifd[tag_id] = val
        except Exception:
            pass

    has_exif = len(raw_exif_dict) > 0

    # Build human-readable tag dictionary
    named_tags: Dict[str, Any] = {}
    for tag_id, val in raw_exif_dict.items():
        name = TAGS.get(tag_id, f"Tag_{tag_id}")
        named_tags[name] = _safe_convert_value(val)

    # Device & Camera Hardware
    make = named_tags.get("Make")
    model = named_tags.get("Model")
    lens_model = named_tags.get("LensModel") or named_tags.get("LensInfo")
    software = named_tags.get("Software")

    camera_device = {
        "make": make,
        "model": model,
        "lens_model": lens_model,
        "software": software,
        "has_editing_software": bool(software and any(s in str(software).lower() for s in ["photoshop", "gimp", "lightroom", "paint.net", "canva", "snapseed"])),
    }

    # Timestamps
    date_time_original = named_tags.get("DateTimeOriginal")
    date_time_digitized = named_tags.get("DateTimeDigitized")
    modify_date = named_tags.get("DateTime")

    timestamps = {
        "original": date_time_original,
        "digitized": date_time_digitized,
        "modified": modify_date,
        "has_consistent_timestamps": (
            date_time_original == date_time_digitized
            if date_time_original and date_time_digitized else None
        ),
    }

    # Optical & Exposure settings
    exposure_time = named_tags.get("ExposureTime")
    f_number = named_tags.get("FNumber")
    iso = named_tags.get("ISOSpeedRatings") or named_tags.get("PhotographicSensitivity")
    focal_length = named_tags.get("FocalLength")
    flash = named_tags.get("Flash")
    white_balance = named_tags.get("WhiteBalance")
    orientation = named_tags.get("Orientation")

    # Format exposure time into friendly fraction if decimal
    exposure_formatted = None
    if exposure_time:
        try:
            exp_float = float(exposure_time)
            if 0 < exp_float < 1:
                denom = round(1.0 / exp_float)
                exposure_formatted = f"1/{denom} s"
            else:
                exposure_formatted = f"{exp_float} s"
        except Exception:
            exposure_formatted = str(exposure_time)

    optical_settings = {
        "exposure_time": exposure_formatted or exposure_time,
        "f_number": f"f/{f_number}" if f_number else None,
        "iso": iso,
        "focal_length": f"{focal_length} mm" if focal_length else None,
        "flash": flash,
        "white_balance": white_balance,
        "orientation_code": orientation,
    }

    # Location / GPS Metadata
    gps_data = extract_gps_data(gps_ifd)

    # General / Image Info tags (e.g. ICC profile presence, copyright)
    info_dict: Dict[str, Any] = {}
    for k, v in getattr(img, "info", {}).items():
        if k not in ("exif", "icc_profile"):
            info_dict[str(k)] = _safe_convert_value(v)
    if "icc_profile" in getattr(img, "info", {}):
        info_dict["icc_profile_present"] = True

    return {
        "has_exif": has_exif,
        "total_tags_found": len(raw_exif_dict),
        "camera_device": camera_device,
        "timestamps": timestamps,
        "optical_settings": optical_settings,
        "location": gps_data,
        "additional_info": info_dict,
        "all_tags": named_tags,
        "forensic_note": (
            "EXIF metadata can be stripped, rewritten, or falsified by external software. "
            "Absence of EXIF does not indicate forgery, as social media platforms routinely sanitize metadata. "
            "Conversely, valid EXIF does not certify image authenticity."
        ),
    }
