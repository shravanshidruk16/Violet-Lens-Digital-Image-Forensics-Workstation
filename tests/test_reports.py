import io
import json


def test_full_report_structure(client, sample_jpeg_bytes):
    """Verify that analyzing an image generates a comprehensive report following the schema."""
    data = {
        "image": (io.BytesIO(sample_jpeg_bytes), "evidence_doc.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    json_data = res.get_json()
    exam_id = json_data["examination_id"]

    # Test report JSON download endpoint
    rep_res = client.get(f"/api/examinations/{exam_id}/report.json")
    assert rep_res.status_code == 200
    assert rep_res.content_type == "application/json"
    assert "attachment" in rep_res.headers.get("Content-Disposition", "")

    report = json.loads(rep_res.data.decode("utf-8"))
    assert report["workstation"]["name"] == "Violet Lens — Digital Image Forensics Workstation"
    assert report["examination"]["id"] == exam_id
    assert "sha256" in report["evidence_integrity"]
    assert "file_signature" in report
    assert "image_properties" in report
    assert "metadata_inspection" in report
    assert "error_level_analysis" in report
    assert "pixel_and_color_analysis" in report
    assert "observations" in report
    assert "methodology_and_limitations" in report


def test_html_report_rendering(client, sample_jpeg_bytes):
    """Verify that the browser printable report renders with status 200 and required elements."""
    data = {
        "image": (io.BytesIO(sample_jpeg_bytes), "evidence_doc.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    exam_id = res.get_json()["examination_id"]

    html_res = client.get(f"/examinations/{exam_id}/report")
    assert html_res.status_code == 200
    html_text = html_res.data.decode("utf-8")
    assert "VIOLET LENS" in html_text
    assert exam_id in html_text
    assert "Evidence Ingestion &amp; Cryptographic Integrity" in html_text or "Evidence Ingestion & Cryptographic Integrity" in html_text


def test_invalid_exam_id_rejected(client):
    """Verify that an invalid non-UUID examination ID is rejected with 400."""
    res = client.get("/api/examinations/invalid-id/report.json")
    assert res.status_code == 400


def test_nonexistent_exam_id_returns_404(client):
    """Verify that a valid UUID that does not exist returns 404."""
    dummy_uuid = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/api/examinations/{dummy_uuid}/report.json")
    assert res.status_code == 404
