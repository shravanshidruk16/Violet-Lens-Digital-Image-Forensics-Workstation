/**
 * Violet Lens — Evidence Upload and Ingestion Controller
 * Handles drag-and-drop, client validation, file staging, and asynchronous analysis dispatch.
 */

const MAX_UPLOAD_BYTES = 15 * 1024 * 1024; // 15 MB
const ALLOWED_EXTS = ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'tif'];

class UploadController {
    constructor() {
        this.selectedFile = null;
        this.isAnalyzing = false;
        this._bindElements();
        this._bindEvents();
    }

    _bindElements() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('evidenceFileInput');
        this.browseBtn = document.getElementById('browseFilesBtn');
        this.stagedCard = document.getElementById('stagedFileBox');
        this.stagedName = document.getElementById('stagedFileName');
        this.stagedSize = document.getElementById('stagedFileSize');
        this.clearBtn = document.getElementById('clearSelectionBtn');
        this.analyzeBtn = document.getElementById('analyzeEvidenceBtn');
        this.processingState = document.getElementById('processingState');
        this.processingStatus = document.getElementById('processingStatusText');
        this.errorAlert = document.getElementById('uploadErrorAlert');
        this.errorTitle = document.getElementById('alertErrorTitle');
        this.errorDesc = document.getElementById('alertErrorDesc');
        this.emptyState = document.getElementById('emptyStateSection');
        this.resultsContainer = document.getElementById('resultsContainer');
    }

    _bindEvents() {
        if (!this.dropZone || !this.fileInput) return;

        // Click browse button or dropzone to trigger file input
        this.browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.fileInput.click();
        });

        this.dropZone.addEventListener('click', () => {
            this.fileInput.click();
        });

        this.dropZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.fileInput.click();
            }
        });

        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                this._handleFileSelection(e.target.files[0]);
            }
        });

        // Drag and Drop
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.add('drag-active');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.remove('drag-active');
            });
        });

        this.dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                this._handleFileSelection(dt.files[0]);
            }
        });

        this.clearBtn.addEventListener('click', () => {
            this.clearStagedFile();
        });

        this.analyzeBtn.addEventListener('click', () => {
            this.submitEvidence();
        });
    }

    _formatBytes(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }

    _handleFileSelection(file) {
        this._hideError();
        if (!file) return;

        // Check file extension
        const ext = file.name.split('.').pop().toLowerCase();
        if (!ALLOWED_EXTS.includes(ext)) {
            this._showError(
                'Unsupported File Format',
                `'.${ext}' is not a supported evidence format. Supported formats: JPEG, PNG, WEBP, BMP, TIFF.`
            );
            return;
        }

        // Check file size limit
        if (file.size > MAX_UPLOAD_BYTES) {
            this._showError(
                'File Size Exceeded',
                `Selected evidence file is ${this._formatBytes(file.size)}. Maximum allowable upload size is 15 MB.`
            );
            return;
        }

        if (file.size === 0) {
            this._showError(
                'Empty File Selected',
                'The selected file contains 0 bytes. Please select a valid digital image.'
            );
            return;
        }

        this.selectedFile = file;
        this.stagedName.textContent = file.name;
        this.stagedSize.textContent = `${this._formatBytes(file.size)} (${file.type || 'image/' + ext})`;
        this.stagedCard.style.display = 'flex';
        this.dropZone.style.display = 'none';
    }

    clearStagedFile() {
        this.selectedFile = null;
        this.fileInput.value = '';
        this.stagedCard.style.display = 'none';
        this.dropZone.style.display = 'block';
        this._hideError();
    }

    _showError(title, desc) {
        this.errorTitle.textContent = title;
        this.errorDesc.textContent = desc;
        this.errorAlert.style.display = 'flex';
    }

    _hideError() {
        this.errorAlert.style.display = 'none';
    }

    async submitEvidence() {
        if (!this.selectedFile || this.isAnalyzing) return;

        this.isAnalyzing = true;
        this._hideError();
        this.stagedCard.style.display = 'none';
        this.processingState.style.display = 'flex';
        this.processingStatus.textContent = 'Extracting unaltered byte stream and calculating SHA-256 fingerprint...';

        const formData = new FormData();
        formData.append('image', this.selectedFile);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                const errMsg = result.details || result.error || 'Server rejected the examination request.';
                throw new Error(errMsg);
            }

            // Successfully received forensic analysis package
            this.processingState.style.display = 'none';
            if (this.emptyState) this.emptyState.style.display = 'none';

            if (window.AnalysisController) {
                window.AnalysisController.populateResults(result);
            }

            if (window.app && typeof window.app.showToast === 'function') {
                window.app.showToast('Evidence analyzed successfully. Examination report ready.');
            }

        } catch (err) {
            this.processingState.style.display = 'none';
            this.stagedCard.style.display = 'flex';
            this._showError('Forensic Examination Failed', err.message);
        } finally {
            this.isAnalyzing = false;
        }
    }
}

window.UploadController = UploadController;
