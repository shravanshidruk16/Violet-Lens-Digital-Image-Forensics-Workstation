# Automated & Manual Test Plan — Violet Lens Workstation

## 1. Overview
This test plan provides comprehensive verification procedures for the Violet Lens Digital Image Forensics Workstation. Tests encompass unit-level forensic algorithms, HTTP API endpoints, evidence sanitization, edge cases, and end-to-end user workflows.

---

## 2. Test Execution Commands

### Run Full Test Suite
```powershell
python -m pytest -v
```

### Run Focused Module Tests
```powershell
# Cryptographic integrity tests
python -m pytest tests/test_integrity.py -v

# Error Level Analysis tests
python -m pytest tests/test_ela.py -v

# EXIF and Metadata extraction tests
python -m pytest tests/test_metadata.py -v

# Ingestion and format validation tests
python -m pytest tests/test_upload.py -v

# Report generation tests
python -m pytest tests/test_reports.py -v

# API endpoints and security headers tests
python -m pytest tests/test_api.py -v
```

---

## 3. Test Matrix & Verification Scenarios

| Test ID | Module | Scenario Description | Expected Outcome | Verification Status |
|---|---|---|---|---|
| **TC-01** | `integrity` | SHA-256 calculation on original bytes | Output matches `hashlib.sha256().hexdigest()` bit-for-bit | Automated (Pass) |
| **TC-02** | `integrity` | Pre-acquisition hash preservation | Hash remains based on original bytes despite preview generation | Automated (Pass) |
| **TC-03** | `signature` | Consistent JPEG header verification | Matches `FF D8 FF`, `is_consistent: True` | Automated (Pass) |
| **TC-04** | `signature` | Extension-content mismatch detection | PNG bytes with `.jpg` extension detected as `MISMATCH_DETECTED` | Automated (Pass) |
| **TC-05** | `metadata` | Synthetic EXIF tag parsing | Extracts Make, Model, Software, and GPS decimal coordinates | Automated (Pass) |
| **TC-06** | `metadata` | Image with zero EXIF tags | Returns `has_exif: False` gracefully without runtime errors | Automated (Pass) |
| **TC-07** | `metadata` | Corrupt or malformed EXIF payload | Recovers gracefully, sets neutral fallback note | Automated (Pass) |
| **TC-08** | `ela` | Genuine JPEG ELA generation | Resaves at Q=90, computes mean/max/std error, produces valid PNG | Automated (Pass) |
| **TC-09** | `ela` | Non-JPEG file submitted to ELA | Returns `is_available: False` with clear educational note | Automated (Pass) |
| **TC-10** | `pixel` | Channel histograms and entropy | 256-bin counts, ITU-R BT.601 luma, Shannon entropy calculated | Automated (Pass) |
| **TC-11** | `upload` | Valid JPEG / PNG / WebP / BMP uploads | All return HTTP 200 with complete forensic dictionary | Automated (Pass) |
| **TC-12** | `upload` | Zero-byte empty file upload | Rejection with HTTP 400 Bad Request | Automated (Pass) |
| **TC-13** | `upload` | Arbitrary text masquerading as image | Pillow rejects, returns HTTP 400 with validation message | Automated (Pass) |
| **TC-14** | `reports` | Verifiable JSON export | Returns downloadable JSON conforming to schema | Automated (Pass) |
| **TC-15** | `reports` | Printable HTML examination dossier | Renders clean dossier with attestation block | Automated (Pass) |
| **TC-16** | `security` | Directory traversal attempt in UUID | Blocked with HTTP 400 / 404 | Automated (Pass) |
| **TC-17** | `security` | Defensive HTTP security headers | `X-Content-Type-Options: nosniff` and `X-Frame-Options: SAMEORIGIN` verified | Automated (Pass) |

---

## 4. Manual UI Verification Workflow

### Step 1: Workstation Initialization
1. Start Flask app: `python app.py`
2. Open browser at `http://127.0.0.1:5000/`
3. Verify purple-and-pink theme, deep aubergine sidebar, and Times New Roman typography across all labels.

### Step 2: Evidence Ingestion
1. Drag and drop a valid JPEG image into the drop zone.
2. Confirm staged file card displays correct filename and formatted size.
3. Click "Analyze Image".
4. Verify honest loading spinner and status feedback.

### Step 3: Forensic Inspection
1. Verify SHA-256 hash box is populated; click "Copy Hash" and confirm clipboard copy feedback.
2. Toggle between "Side-by-Side", "Original Only", and "ELA Only" views.
3. Review EXIF tabs: Summary, Geolocation (test "Reveal Coordinates Locally"), and All Tags filter.
4. Review interactive Canvas histogram; toggle channels (Red, Green, Blue, Luminance).
5. Review deterministic findings categorized into Info, Review, and Limitation.

### Step 4: Dossier Export & Print Preview
1. Click "Download JSON Report" — verify downloaded `.json` file contains complete analysis data.
2. Click "Export Examination Report" — verify new tab opens `/examinations/<id>/report` with formal dossier layout.
3. Click "Print or Save as PDF" — verify print preview displays clean white background, proper tables, and attestation block.

### Step 5: New Examination Lifecycle
1. Click "New Examination".
2. Confirm state resets completely, results are cleared, and upload drop zone is ready for subsequent evidence.
