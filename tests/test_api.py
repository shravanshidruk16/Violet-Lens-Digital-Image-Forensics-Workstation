import io


def test_index_route(client):
    """Verify main index page returns 200 with Violet Lens branding."""
    res = client.get("/")
    assert res.status_code == 200
    content = res.data.decode("utf-8")
    assert "VIOLET LENS" in content
    assert "Image Forensics Workspace" in content


def test_health_route(client):
    """Verify diagnostics health endpoint returns healthy status and supported formats."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert "supported_formats" in data
    assert "jpeg" in data["supported_formats"] or "jpg" in data["supported_formats"]


def test_ela_image_endpoint(client, sample_jpeg_bytes):
    """Verify retrieving the generated ELA visualization PNG."""
    data = {
        "image": (io.BytesIO(sample_jpeg_bytes), "sample.jpg")
    }
    res = client.post("/api/analyze", data=data, content_type="multipart/form-data")
    assert res.status_code == 200
    exam_id = res.get_json()["examination_id"]

    ela_res = client.get(f"/api/examinations/{exam_id}/ela")
    assert ela_res.status_code == 200
    assert ela_res.content_type == "image/png"


def test_security_headers_present(client):
    """Ensure defensive security headers are applied to HTTP responses."""
    res = client.get("/")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert "strict-origin" in res.headers.get("Referrer-Policy", "")


def test_path_traversal_prevention(client):
    """Ensure attempted directory traversal in examination ID is blocked with 400."""
    res = client.get("/api/examinations/../../etc/passwd/report.json")
    assert res.status_code in (400, 404)
