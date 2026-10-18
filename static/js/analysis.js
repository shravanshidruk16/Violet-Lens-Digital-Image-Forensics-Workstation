/**
 * Violet Lens — Forensic Analysis Presentation Controller
 * Renders verified forensic results across integrity, visual ELA, metadata,
 * radiometric pixel distributions, and deterministic observations.
 */

class AnalysisController {
    constructor() {
        this.currentData = null;
        this.histogramRenderer = null;
        this._bindElements();
        this._bindEvents();
    }

    _bindElements() {
        this.resultsContainer = document.getElementById('resultsContainer');
        this.emptyState = document.getElementById('emptyStateSection');
        this.uploadCard = document.getElementById('uploadSection');

        // Top Action Bar
        this.examIdDisplay = document.getElementById('resExamIdDisplay');
        this.examTimestamp = document.getElementById('resExamTimestamp');
        this.newExamBtn = document.getElementById('newExaminationBtn');
        this.downloadJsonBtn = document.getElementById('downloadJsonBtn');
        this.printReportBtn = document.getElementById('printReportBtn');
        this.bottomDownloadJsonBtn = document.getElementById('bottomDownloadJsonBtn');
        this.bottomPrintReportBtn = document.getElementById('bottomPrintReportBtn');

        // Integrity
        this.sha256Value = document.getElementById('resSha256Value');
        this.copyShaBtn = document.getElementById('copyShaBtn');
        this.copyShaText = document.getElementById('copyShaBtnText');
        this.originalFilename = document.getElementById('resOriginalFilename');
        this.byteSize = document.getElementById('resByteSize');
        this.magicBytes = document.getElementById('resMagicBytes');
        this.extensionConsistency = document.getElementById('resExtensionConsistency');

        // Dual Viewport & ELA
        this.dualViewportGrid = document.getElementById('dualViewportGrid');
        this.viewSideBySideBtn = document.getElementById('viewSideBySideBtn');
        this.viewOriginalBtn = document.getElementById('viewOriginalBtn');
        this.viewElaBtn = document.getElementById('viewElaBtn');
        this.originalViewportBox = document.getElementById('originalViewportBox');
        this.elaViewportBox = document.getElementById('elaViewportBox');
        this.originalFormatBadge = document.getElementById('originalFormatBadge');
        this.originalEvidenceImg = document.getElementById('originalEvidenceImg');
        this.elaResultImg = document.getElementById('elaResultImg');
        this.elaUnavailableBox = document.getElementById('elaUnavailableBox');
        this.elaUnavailableReason = document.getElementById('elaUnavailableReason');
        this.elaMetricsBar = document.getElementById('elaMetricsBar');
        this.elaMeanErrorVal = document.getElementById('elaMeanErrorVal');
        this.elaMaxErrorVal = document.getElementById('elaMaxErrorVal');
        this.elaStdErrorVal = document.getElementById('elaStdErrorVal');
        this.elaHighErrorVal = document.getElementById('elaHighErrorVal');
        this.elaScientificNote = document.getElementById('elaScientificNote');

        // Properties Table
        this.propertiesTableBody = document.getElementById('propertiesTableBody');

        // Metadata Tabs & Content
        this.metaTabSummaryBtn = document.getElementById('metaTabSummaryBtn');
        this.metaTabGpsBtn = document.getElementById('metaTabGpsBtn');
        this.metaTabAllTagsBtn = document.getElementById('metaTabAllTagsBtn');
        this.metaPaneSummary = document.getElementById('metaPaneSummary');
        this.metaPaneGps = document.getElementById('metaPaneGps');
        this.metaPaneAllTags = document.getElementById('metaPaneAllTags');
        this.metadataCountBadge = document.getElementById('metadataCountBadge');
        this.allTagsTableBody = document.getElementById('allTagsTableBody');
        this.metaSearchInput = document.getElementById('metaSearchInput');

        // GPS Disclosure Controls
        this.gpsDataContainer = document.getElementById('gpsDataContainer');
        this.gpsAbsentContainer = document.getElementById('gpsAbsentContainer');
        this.gpsStatusSubText = document.getElementById('gpsStatusSubText');
        this.gpsShieldedState = document.getElementById('gpsShieldedState');
        this.gpsRevealedState = document.getElementById('gpsRevealedState');
        this.revealCoordinatesBtn = document.getElementById('revealCoordinatesBtn');
        this.hideCoordinatesBtn = document.getElementById('hideCoordinatesBtn');
        this.revealedCoordsText = document.getElementById('revealedCoordsText');
        this.revealedAltText = document.getElementById('revealedAltText');
        this.openMapLink = document.getElementById('openMapLink');

        // Pixel Analysis
        this.pixelStatsTableBody = document.getElementById('pixelStatsTableBody');
        this.channelBtns = document.querySelectorAll('.channel-btn');

        // Observations List
        this.observationsList = document.getElementById('observationsList');
    }

    _bindEvents() {
        // Copy SHA-256 button
        this.copyShaBtn.addEventListener('click', () => {
            if (!this.currentData) return;
            const sha = this.currentData.integrity.sha256_hash;
            navigator.clipboard.writeText(sha).then(() => {
                this.copyShaText.textContent = 'Copied!';
                setTimeout(() => {
                    this.copyShaText.textContent = 'Copy Hash';
                }, 2000);
                if (window.app && typeof window.app.showToast === 'function') {
                    window.app.showToast('SHA-256 hash copied to clipboard.');
                }
            }).catch(() => {
                this.copyShaText.textContent = 'Failed';
            });
        });

        // View Mode Toggles (Side-by-side, Original, ELA)
        this.viewSideBySideBtn.addEventListener('click', () => this._setViewMode('side-by-side'));
        this.viewOriginalBtn.addEventListener('click', () => this._setViewMode('original'));
        this.viewElaBtn.addEventListener('click', () => this._setViewMode('ela'));

        // Metadata Subtabs
        this.metaTabSummaryBtn.addEventListener('click', () => this._setMetaSubtab('summary'));
        this.metaTabGpsBtn.addEventListener('click', () => this._setMetaSubtab('gps'));
        this.metaTabAllTagsBtn.addEventListener('click', () => this._setMetaSubtab('all-tags'));

        // GPS Privacy Disclosure Toggles
        this.revealCoordinatesBtn.addEventListener('click', () => {
            this.gpsShieldedState.style.display = 'none';
            this.gpsRevealedState.style.display = 'block';
        });

        this.hideCoordinatesBtn.addEventListener('click', () => {
            this.gpsRevealedState.style.display = 'none';
            this.gpsShieldedState.style.display = 'block';
        });

        // EXIF Search Filter
        this.metaSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = this.allTagsTableBody.querySelectorAll('tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });

        // Channel Toggles for Canvas Histogram
        this.channelBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.channelBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const ch = btn.getAttribute('data-channel');
                if (this.histogramRenderer) {
                    this.histogramRenderer.setChannelFilter(ch);
                }
            });
        });

        // New Examination Action
        this.newExamBtn.addEventListener('click', () => this.resetWorkspace());
    }

    _setViewMode(mode) {
        [this.viewSideBySideBtn, this.viewOriginalBtn, this.viewElaBtn].forEach(b => b.classList.remove('active'));

        if (mode === 'side-by-side') {
            this.viewSideBySideBtn.classList.add('active');
            this.dualViewportGrid.style.gridTemplateColumns = '1fr 1fr';
            this.originalViewportBox.style.display = 'flex';
            this.elaViewportBox.style.display = 'flex';
        } else if (mode === 'original') {
            this.viewOriginalBtn.classList.add('active');
            this.dualViewportGrid.style.gridTemplateColumns = '1fr';
            this.originalViewportBox.style.display = 'flex';
            this.elaViewportBox.style.display = 'none';
        } else if (mode === 'ela') {
            this.viewElaBtn.classList.add('active');
            this.dualViewportGrid.style.gridTemplateColumns = '1fr';
            this.originalViewportBox.style.display = 'none';
            this.elaViewportBox.style.display = 'flex';
        }
    }

    _setMetaSubtab(subtab) {
        [this.metaTabSummaryBtn, this.metaTabGpsBtn, this.metaTabAllTagsBtn].forEach(b => b.classList.remove('active'));
        [this.metaPaneSummary, this.metaPaneGps, this.metaPaneAllTags].forEach(p => p.style.display = 'none');

        if (subtab === 'summary') {
            this.metaTabSummaryBtn.classList.add('active');
            this.metaPaneSummary.style.display = 'block';
        } else if (subtab === 'gps') {
            this.metaTabGpsBtn.classList.add('active');
            this.metaPaneGps.style.display = 'block';
        } else if (subtab === 'all-tags') {
            this.metaTabAllTagsBtn.classList.add('active');
            this.metaPaneAllTags.style.display = 'block';
        }
    }

    populateResults(data) {
        this.currentData = data;
        const { integrity, properties, signature, metadata, ela, pixels, observations } = data;

        // Reveal results container
        this.resultsContainer.style.display = 'flex';
        this.emptyState.style.display = 'none';

        // 1. Top Action Bar & Identifiers
        this.examIdDisplay.textContent = integrity.examination_id.substring(0, 13) + '...';
        this.examIdDisplay.title = integrity.examination_id;
        this.examTimestamp.textContent = integrity.timestamp_utc.replace('T', ' ').substring(0, 19) + ' UTC';

        this.downloadJsonBtn.href = data.report_download_url;
        this.printReportBtn.href = data.report_view_url;
        this.bottomDownloadJsonBtn.href = data.report_download_url;
        this.bottomPrintReportBtn.href = data.report_view_url;

        // 2. Integrity Section
        this.sha256Value.textContent = integrity.sha256_hash;
        this.originalFilename.textContent = integrity.original_filename;
        this.byteSize.textContent = `${integrity.byte_size_formatted} (${integrity.byte_size.toLocaleString()} bytes)`;
        this.magicBytes.textContent = signature.magic_bytes_hex;

        if (signature.is_consistent) {
            this.extensionConsistency.innerHTML = `
                <span class="badge-status-verified">CONSISTENT</span>
                <span style="margin-left: 6px; font-size: 0.9rem;">.${signature.claimed_extension} matches ${signature.detected_signature_format} header</span>
            `;
        } else {
            this.extensionConsistency.innerHTML = `
                <span class="badge-status-warning">MISMATCH DETECTED</span>
                <span style="margin-left: 6px; font-size: 0.9rem; color: #8F5B10;">.${signature.claimed_extension} claim vs ${signature.detected_signature_format} header</span>
            `;
        }

        // 3. Dual Viewport & ELA
        this.originalEvidenceImg.src = data.preview_data_uri;
        this.originalFormatBadge.textContent = `${properties.format} &bull; ${properties.mode}`;

        if (ela.is_available) {
            this.elaResultImg.src = ela.data_uri;
            this.elaResultImg.style.display = 'block';
            this.elaUnavailableBox.style.display = 'none';
            this.elaMetricsBar.style.display = 'grid';

            this.elaMeanErrorVal.textContent = ela.mean_error;
            this.elaMaxErrorVal.textContent = ela.max_error;
            this.elaStdErrorVal.textContent = ela.std_error;
            this.elaHighErrorVal.textContent = `${ela.high_error_pixel_percentage}%`;
            this.elaScientificNote.textContent = ela.scientific_note;
        } else {
            this.elaResultImg.style.display = 'none';
            this.elaUnavailableBox.style.display = 'block';
            this.elaUnavailableReason.textContent = ela.reason || 'Not applicable to this image encoding format.';
            this.elaMetricsBar.style.display = 'none';
            this.elaScientificNote.textContent = 'Error Level Analysis is intentionally restricted to JPEG sources to prevent false or misleading forensic artifacts.';
        }

        // 4. Properties Table
        this._renderPropertiesTable(properties);

        // 5. Metadata Subtabs & Summary
        this._renderMetadata(metadata);

        // 6. Pixel & Color Histograms
        this._renderPixelAnalysis(pixels);

        // 7. Deterministic Observations
        this._renderObservations(observations);

        // Scroll to results cleanly
        this.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    _renderPropertiesTable(props) {
        const rows = [
            { prop: 'Pixel Dimensions', val: props.dimensions, sig: 'Native resolution grid (Width × Height)' },
            { prop: 'Megapixel Count', val: `${props.megapixels} MP`, sig: 'Total sensor or canvas sample volume' },
            { prop: 'Aspect Ratio', val: props.aspect_ratio, sig: 'Geometric aspect proportion' },
            { prop: 'Decoded Format', val: props.format, sig: 'Pillow-decoded raster specification' },
            { prop: 'Color Mode', val: props.mode, sig: 'Pixel channel encoding representation' },
            { prop: 'Channel Count', val: props.channels.toString(), sig: 'Number of individual color/alpha planes' },
            { prop: 'Transparency Support', val: props.has_transparency ? 'Yes (Alpha channel active)' : 'No (Fully opaque)', sig: 'Indicates potential composition layers' },
            { prop: 'Frame Count', val: props.frame_count.toString(), sig: props.is_animated ? 'Multi-frame container' : 'Single static raster' }
        ];

        this.propertiesTableBody.innerHTML = rows.map(r => `
            <tr>
                <td style="font-weight: 700; color: #28152F;">${r.prop}</td>
                <td class="mono">${r.val}</td>
                <td style="color: #716779;">${r.sig}</td>
            </tr>
        `).join('');
    }

    _renderMetadata(meta) {
        this.metadataCountBadge.textContent = `${meta.total_tags_found} Tags Extracted`;

        // Camera Summary
        const cam = meta.camera_device || {};
        document.getElementById('resMetaMake').textContent = cam.make || 'Not Present';
        document.getElementById('resMetaModel').textContent = cam.model || 'Not Present';
        document.getElementById('resMetaLens').textContent = cam.lens_model || 'Not Present';
        
        const swEl = document.getElementById('resMetaSoftware');
        if (cam.software) {
            swEl.innerHTML = `<strong style="color: #28152F;">${cam.software}</strong>` +
                (cam.has_editing_software ? ' <span class="tag-badge" style="background:#FFF3E0;color:#E65100;border-color:#FFE0B2;">Editing Software</span>' : '');
        } else {
            swEl.textContent = 'Not Recorded';
        }

        // Timestamps
        const ts = meta.timestamps || {};
        document.getElementById('resMetaTimeOrig').textContent = ts.original || 'Not Present';
        document.getElementById('resMetaTimeDig').textContent = ts.digitized || 'Not Present';
        document.getElementById('resMetaTimeMod').textContent = ts.modified || 'Not Present';

        const statusEl = document.getElementById('resMetaTimeStatus');
        if (ts.has_consistent_timestamps === true) {
            statusEl.innerHTML = '<span class="badge-status-verified" style="font-size:0.75rem;">Timestamps Synchronized</span>';
        } else if (ts.has_consistent_timestamps === false) {
            statusEl.innerHTML = '<span class="badge-status-warning" style="font-size:0.75rem;">Modification Timestamp Divergence</span>';
        } else {
            statusEl.textContent = 'Incomplete timestamp pair';
        }

        // Optics
        const opt = meta.optical_settings || {};
        document.getElementById('resMetaExp').textContent = opt.exposure_time || 'Not Present';
        document.getElementById('resMetaAperture').textContent = opt.f_number || 'Not Present';
        document.getElementById('resMetaIso').textContent = opt.iso || 'Not Present';
        document.getElementById('resMetaFocal').textContent = opt.focal_length || 'Not Present';
        document.getElementById('resMetaFlash').textContent = opt.flash !== null ? String(opt.flash) : 'Not Present';

        // GPS Geolocation
        const gps = meta.location || {};
        const gpsPresenceEl = document.getElementById('resMetaGpsPresence');

        if (gps.has_gps) {
            gpsPresenceEl.innerHTML = '<span class="badge-status-verified" style="font-size:0.75rem;">Coordinates Present (Masked)</span>';
            this.gpsStatusSubText.textContent = 'Embedded EXIF GPS metadata detected.';
            this.gpsDataContainer.style.display = 'block';
            this.gpsAbsentContainer.style.display = 'none';

            if (gps.has_coordinates) {
                this.revealedCoordsText.textContent = gps.coordinates_formatted || `${gps.latitude_decimal}, ${gps.longitude_decimal}`;
                this.revealedAltText.textContent = gps.altitude ? `Altitude: ${gps.altitude}` : '';
                this.openMapLink.href = `https://www.google.com/maps?q=${gps.latitude_decimal},${gps.longitude_decimal}`;
            } else {
                this.revealedCoordsText.textContent = 'GPS IFD present but coordinate tags unresolvable.';
                this.openMapLink.style.display = 'none';
            }
        } else {
            gpsPresenceEl.textContent = 'Not Present';
            this.gpsStatusSubText.textContent = 'No geolocation parameters detected in file stream.';
            this.gpsDataContainer.style.display = 'none';
            this.gpsAbsentContainer.style.display = 'block';
        }

        // All Tags Table
        const allTags = meta.all_tags || {};
        const tagEntries = Object.entries(allTags);
        if (tagEntries.length === 0) {
            this.allTagsTableBody.innerHTML = '<tr><td colspan="2" style="text-align: center; color: #716779;">No readable EXIF tags identified in file stream.</td></tr>';
        } else {
            this.allTagsTableBody.innerHTML = tagEntries.map(([k, v]) => `
                <tr>
                    <td class="mono" style="font-weight: 700; color: #28152F;">${k}</td>
                    <td style="word-break: break-all;">${typeof v === 'object' ? JSON.stringify(v) : v}</td>
                </tr>
            `).join('');
        }
    }

    _renderPixelAnalysis(pixels) {
        // Initialize or update canvas renderer
        if (!this.histogramRenderer) {
            this.histogramRenderer = new window.HistogramRenderer('histogramCanvas');
        }
        this.histogramRenderer.setHistograms(pixels.histograms);

        // Populate Channel Statistics Table
        const stats = pixels.channel_statistics || {};
        const rows = Object.entries(stats).map(([chName, s]) => `
            <tr>
                <td style="font-weight: 700; text-transform: capitalize; color: #28152F;">${chName}</td>
                <td class="mono">${s.mean}</td>
                <td class="mono">${s.std}</td>
                <td class="mono">${s.min} / ${s.max}</td>
                <td class="mono" style="${s.shadow_clipping_pct > 10 ? 'color: #8F5B10; font-weight: 700;' : ''}">${s.shadow_clipping_pct}%</td>
                <td class="mono" style="${s.highlight_clipping_pct > 10 ? 'color: #8F5B10; font-weight: 700;' : ''}">${s.highlight_clipping_pct}%</td>
                <td class="mono" style="font-weight: 700; color: #7450C8;">${s.entropy_bits}</td>
            </tr>
        `).join('');

        this.pixelStatsTableBody.innerHTML = rows;
    }

    _renderObservations(obsList) {
        if (!Array.isArray(obsList) || obsList.length === 0) {
            this.observationsList.innerHTML = '<p class="text-secondary">No observations generated.</p>';
            return;
        }

        this.observationsList.innerHTML = obsList.map(item => {
            const cat = item.category || 'info';
            return `
                <div class="observation-card">
                    <span class="obs-tag-pill obs-tag-${cat}">${cat}</span>
                    <div class="obs-card-content">
                        <strong class="obs-title">${item.title}</strong>
                        <p class="obs-desc">${item.description}</p>
                    </div>
                </div>
            `;
        }).join('');
    }

    resetWorkspace() {
        this.currentData = null;
        this.resultsContainer.style.display = 'none';
        this.emptyState.style.display = 'block';

        if (window.uploadController) {
            window.uploadController.clearStagedFile();
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

window.AnalysisController = AnalysisController;
