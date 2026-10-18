import json
import os
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_file,
    Response,
    abort,
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config
from forensic.integrity import inspect_file_integrity
from forensic.file_signature import check_format_consistency
from forensic.image_loader import load_and_inspect_image, generate_display_preview
from forensic.metadata import extract_metadata
from forensic.ela import perform_error_level_analysis
from forensic.pixel_analysis import analyze_pixels
from forensic.observations import generate_forensic_observations
from forensic.report import generate_examination_report

# UUID validation pattern to prevent path traversal or injection attacks
UUID_PATTERN = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")

def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure isolated examination directory exists
    examinations_dir = Path(app.config["EXAMINATIONS_DIR"])
    examinations_dir.mkdir(parents=True, exist_ok=True)

    # In-memory session cache for rapid preview retrieval, backed by disk storage
    active_examinations: Dict[str, Dict[str, Any]] = {}

    def _cleanup_expired_examinations():
        """Clean up examinations older than the configured TTL."""
        now = time.time()
        ttl = app.config["EXAMINATION_TTL_SECONDS"]
        
        # Purge memory cache
        expired_keys = [
            k for k, v in active_examinations.items()
            if now - v.get("_cached_at", 0) > ttl
        ]
        for k in expired_keys:
            active_examinations.pop(k, None)

        # Purge disk files
        try:
            for file_path in examinations_dir.glob("*.json"):
                if now - file_path.stat().st_mtime > ttl:
                    file_path.unlink(missing_ok=True)
            for file_path in examinations_dir.glob("*.png"):
                if now - file_path.stat().st_mtime > ttl:
                    file_path.unlink(missing_ok=True)
        except Exception:
            pass

    def _get_examination(exam_id: str) -> Optional[Dict[str, Any]]:
        """Safely retrieve examination record by validated UUID."""
        if not UUID_PATTERN.match(exam_id):
            return None
        
        # Check active memory cache
        if exam_id in active_examinations:
            return active_examinations[exam_id]

        # Check isolated disk cache
        exam_file = examinations_dir / f"{exam_id}.json"
        if exam_file.is_file():
            try:
                with open(exam_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    active_examinations[exam_id] = data
                    return data
            except Exception:
                return None
        return None

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        """Apply defensive security headers to all responses."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    @app.route("/")
    def index():
        """Render the main Violet Lens Workstation interface."""
        return render_template("index.html")

    @app.route("/api/health", methods=["GET"])
    def api_health():
        """Health diagnostics endpoint confirming operational status."""
        return jsonify({
            "status": "healthy",
            "application": "Violet Lens — Digital Image Forensics Workstation",
            "version": "1.0.0",
            "supported_formats": sorted(list(app.config["ALLOWED_EXTENSIONS"])),
            "max_upload_bytes": app.config["MAX_CONTENT_LENGTH"],
            "environment": "local_offline",
        })

    @app.route("/api/analyze", methods=["POST"])
    def api_analyze():
        """Execute the primary image forensics pipeline.
        
        Performs byte hashing, format checking, metadata extraction,
        Error Level Analysis (ELA), and radiometric pixel statistics.
        """
        _cleanup_expired_examinations()

        if "image" not in request.files:
            return jsonify({
                "error": "No image payload received.",
                "details": "The multipart request must include an 'image' file field.",
            }), 400

        file = request.files["image"]
        if not file or file.filename == "":
            return jsonify({
                "error": "No file selected.",
                "details": "Please select a valid image file to upload.",
            }), 400

        raw_filename = file.filename or "unknown_evidence.bin"
        safe_name = secure_filename(raw_filename)
        if not safe_name:
            safe_name = "evidence_file.bin"

        # Read exact original bytes
        try:
            raw_bytes = file.read()
        except Exception as e:
            return jsonify({
                "error": "Failed to read uploaded file stream.",
                "details": str(e),
            }), 400

        if len(raw_bytes) == 0:
            return jsonify({
                "error": "Uploaded file is empty (0 bytes).",
                "details": "Cannot conduct forensic analysis on a zero-byte payload.",
            }), 400

        if len(raw_bytes) > app.config["MAX_CONTENT_LENGTH"]:
            return jsonify({
                "error": "File size exceeds workstation limit.",
                "details": f"Maximum allowable upload is {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)} MB.",
            }), 413

        # STEP 1: Compute File Integrity Hash directly from unaltered byte stream
        integrity = inspect_file_integrity(raw_bytes, safe_name)
        exam_id = integrity["examination_id"]

        # STEP 2: Decode and inspect image safely with Pillow
        try:
            pil_img, properties = load_and_inspect_image(raw_bytes)
        except ValueError as ve:
            return jsonify({
                "error": "Image validation failed.",
                "details": str(ve),
                "integrity_record": integrity,
            }), 400
        except Exception as ex:
            return jsonify({
                "error": "Internal decoding failure.",
                "details": "The provided image stream could not be safely rendered or verified.",
            }), 400

        # STEP 3: Verify binary signature and format consistency
        signature = check_format_consistency(
            raw_bytes,
            safe_name,
            properties.get("format")
        )

        # STEP 4: Inspect EXIF and structural metadata
        metadata = extract_metadata(pil_img, raw_bytes)

        # STEP 5: Generate Error Level Analysis (ELA) for JPEG
        ela = perform_error_level_analysis(
            pil_img,
            properties.get("format", ""),
            jpeg_quality=app.config["ELA_JPEG_QUALITY"],
            scale_factor=app.config["ELA_SCALE_FACTOR"],
        )

        # If ELA produced raw PNG bytes, save to cache file for dedicated retrieval
        if ela.get("raw_png_bytes"):
            ela_bytes = ela.pop("raw_png_bytes")
            ela_path = examinations_dir / f"{exam_id}_ela.png"
            try:
                with open(ela_path, "wb") as f:
                    f.write(ela_bytes)
            except Exception:
                pass

        # STEP 6: Compute pixel histograms, entropy, and radiometric clipping
        pixels = analyze_pixels(pil_img)

        # STEP 7: Produce separate safe browser preview
        preview_data_uri = generate_display_preview(pil_img)

        # STEP 8: Synthesize forensic observations
        observations = generate_forensic_observations(
            integrity, properties, signature, metadata, ela, pixels
        )

        # STEP 9: Build complete examination report
        report = generate_examination_report(
            integrity, properties, signature, metadata, ela, pixels, observations
        )

        # Store report record on disk for download and browser print view
        exam_record = {
            "report": report,
            "preview_data_uri": preview_data_uri,
            "ela_preview_data_uri": ela.get("preview_data_uri"),
            "_cached_at": time.time(),
        }
        active_examinations[exam_id] = exam_record

        record_file = examinations_dir / f"{exam_id}.json"
        try:
            with open(record_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
        except Exception:
            pass

        # Return full client analysis package
        response_data = {
            "examination_id": exam_id,
            "integrity": integrity,
            "properties": properties,
            "signature": signature,
            "metadata": metadata,
            "ela": {
                "is_available": ela.get("is_available"),
                "reason": ela.get("reason"),
                "quality": ela.get("quality"),
                "scale": ela.get("scale"),
                "mean_error": ela.get("mean_error"),
                "max_error": ela.get("max_error"),
                "std_error": ela.get("std_error"),
                "high_error_pixel_percentage": ela.get("high_error_pixel_percentage"),
                "scientific_note": ela.get("scientific_note"),
                "preview_url": f"/api/examinations/{exam_id}/ela" if ela.get("is_available") else None,
                "data_uri": ela.get("preview_data_uri"),
            },
            "pixels": pixels,
            "observations": observations,
            "preview_data_uri": preview_data_uri,
            "report_download_url": f"/api/examinations/{exam_id}/report.json",
            "report_view_url": f"/examinations/{exam_id}/report",
        }

        return jsonify(response_data), 200

    @app.route("/api/examinations/<exam_id>/ela", methods=["GET"])
    def get_ela_image(exam_id: str):
        """Serve generated ELA visualization PNG for an active examination."""
        if not UUID_PATTERN.match(exam_id):
            abort(400, description="Invalid examination identifier.")

        ela_path = examinations_dir / f"{exam_id}_ela.png"
        if not ela_path.is_file():
            abort(404, description="ELA visualization not found or expired for this examination.")

        return send_file(ela_path, mimetype="image/png")

    @app.route("/api/examinations/<exam_id>/report.json", methods=["GET"])
    def download_report_json(exam_id: str):
        """Export examination report as a verifiable JSON document."""
        if not UUID_PATTERN.match(exam_id):
            abort(400, description="Invalid examination identifier.")

        exam = _get_examination(exam_id)
        if not exam:
            abort(404, description="Examination report not found or expired.")

        report_data = exam.get("report", exam)
        filename = f"violet-lens-report-{exam_id[:8]}.json"
        
        json_bytes = json.dumps(report_data, indent=2).encode("utf-8")
        return Response(
            json_bytes,
            mimetype="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    @app.route("/examinations/<exam_id>/report", methods=["GET"])
    def render_examination_report(exam_id: str):
        """Render printable examination report view with print-tailored CSS."""
        if not UUID_PATTERN.match(exam_id):
            abort(400, description="Invalid examination identifier.")

        exam = _get_examination(exam_id)
        if not exam:
            abort(404, description="Examination report not found or expired.")

        report_data = exam.get("report", exam)
        preview_uri = exam.get("preview_data_uri")
        ela_uri = exam.get("ela_preview_data_uri")

        return render_template(
            "report.html",
            report=report_data,
            preview_uri=preview_uri,
            ela_uri=ela_uri,
        )

    # Clean error handlers
    @app.errorhandler(400)
    def handle_bad_request(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Bad Request", "details": str(e.description)}), 400
        return render_template("errors/400.html", error=e), 400

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not Found", "details": str(e.description)}), 404
        return render_template("errors/404.html", error=e), 404

    @app.errorhandler(413)
    def handle_too_large(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Payload Too Large",
                "details": f"File exceeds the maximum allowable limit of {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)} MB."
            }), 413
        return render_template("errors/400.html", error="Uploaded file exceeds 15 MB limit."), 413

    @app.errorhandler(500)
    def handle_server_error(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Internal Processing Error",
                "details": "A server-side error occurred during forensic analysis."
            }), 500
        return render_template("errors/500.html", error=e), 500

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(
        host=application.config["HOST"],
        port=application.config["PORT"],
        debug=application.config["DEBUG"],
    )
