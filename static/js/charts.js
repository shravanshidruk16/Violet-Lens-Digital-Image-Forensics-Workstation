/**
 * Violet Lens — HTML5 Canvas Histogram & Pixel Chart Engine
 * Renders actual 256-bin channel histograms in project purple-and-pink aesthetic.
 */

class HistogramRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.currentHistograms = null;
        this.activeChannel = 'all'; // 'all', 'red', 'green', 'blue', 'luminance'
        this.colors = {
            red: '#D32F2F',
            green: '#2E7D32',
            blue: '#1976D2',
            luminance: '#7450C8',
            grid: '#E6DDEA',
            axisText: '#716779',
            bg: '#FFFFFF'
        };
        this._setupHiDPI();
    }

    _setupHiDPI() {
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        const displayWidth = rect.width || 900;
        const displayHeight = 280;

        this.canvas.width = displayWidth * dpr;
        this.canvas.height = displayHeight * dpr;
        this.canvas.style.width = `${displayWidth}px`;
        this.canvas.style.height = `${displayHeight}px`;

        this.ctx.scale(dpr, dpr);
        this.width = displayWidth;
        this.height = displayHeight;
    }

    setHistograms(histograms) {
        this.currentHistograms = histograms;
        this.render();
    }

    setChannelFilter(channel) {
        this.activeChannel = channel;
        this.render();
    }

    render() {
        if (!this.ctx || !this.currentHistograms) return;
        this._setupHiDPI();

        const ctx = this.ctx;
        const w = this.width;
        const h = this.height;
        const padding = { top: 20, right: 30, bottom: 40, left: 55 };
        const chartW = w - padding.left - padding.right;
        const chartH = h - padding.top - padding.bottom;

        // Clear canvas
        ctx.clearRect(0, 0, w, h);

        // Find maximum bin count across visible channels for normalization
        let maxCount = 1;
        const channelsToInspect = (this.activeChannel === 'all')
            ? ['red', 'green', 'blue', 'luminance']
            : [this.activeChannel];

        channelsToInspect.forEach(ch => {
            const arr = this.currentHistograms[ch];
            if (Array.isArray(arr)) {
                // Ignore extreme 0/255 clipping spike if needed for vertical scale, but keep visible
                const localMax = Math.max(...arr);
                if (localMax > maxCount) maxCount = localMax;
            }
        });

        // Draw horizontal grid lines & labels
        ctx.font = '12px "Times New Roman", Times, serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = this.colors.axisText;
        ctx.strokeStyle = this.colors.grid;
        ctx.lineWidth = 1;

        const gridSteps = 4;
        for (let i = 0; i <= gridSteps; i++) {
            const yRatio = i / gridSteps;
            const y = padding.top + chartH * (1 - yRatio);
            const valLabel = Math.round(maxCount * yRatio);

            ctx.beginPath();
            ctx.moveTo(padding.left, y);
            ctx.lineTo(w - padding.right, y);
            ctx.stroke();

            ctx.fillText(valLabel.toLocaleString(), padding.left - 8, y);
        }

        // Draw vertical intensity markers (0, 64, 128, 192, 255)
        const xTicks = [0, 64, 128, 192, 255];
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';

        xTicks.forEach(tick => {
            const x = padding.left + (tick / 255) * chartW;
            ctx.beginPath();
            ctx.moveTo(x, padding.top);
            ctx.lineTo(x, h - padding.bottom);
            ctx.stroke();

            ctx.fillText(tick.toString(), x, h - padding.bottom + 8);
        });

        // X-axis label
        ctx.textAlign = 'center';
        ctx.fillText('Pixel Intensity Level (0 – 255)', padding.left + chartW / 2, h - 14);

        // Draw Channel Curves
        const channelsToDraw = (this.activeChannel === 'all')
            ? [
                { key: 'red', color: this.colors.red, alpha: 0.8 },
                { key: 'green', color: this.colors.green, alpha: 0.8 },
                { key: 'blue', color: this.colors.blue, alpha: 0.8 },
                { key: 'luminance', color: this.colors.luminance, alpha: 0.95 }
              ]
            : [{ key: this.activeChannel, color: this.colors[this.activeChannel] || '#7450C8', alpha: 1.0 }];

        channelsToDraw.forEach(chObj => {
            const arr = this.currentHistograms[chObj.key];
            if (!Array.isArray(arr) || arr.length === 0) return;

            ctx.save();
            ctx.strokeStyle = chObj.color;
            ctx.fillStyle = chObj.color;
            ctx.lineWidth = (chObj.key === 'luminance' || this.activeChannel !== 'all') ? 2 : 1.5;
            ctx.globalAlpha = chObj.alpha;

            // Plot polygon
            ctx.beginPath();
            ctx.moveTo(padding.left, h - padding.bottom);

            for (let i = 0; i < 256; i++) {
                const val = arr[i] || 0;
                const x = padding.left + (i / 255) * chartW;
                const y = padding.top + chartH - (val / maxCount) * chartH;
                if (i === 0) {
                    ctx.lineTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }

            ctx.lineTo(padding.left + chartW, h - padding.bottom);
            ctx.closePath();

            // Fill area with subtle translucent wash
            ctx.globalAlpha = (this.activeChannel === 'all') ? 0.08 : 0.2;
            ctx.fill();

            // Draw clean stroke line
            ctx.globalAlpha = chObj.alpha;
            ctx.beginPath();
            for (let i = 0; i < 256; i++) {
                const val = arr[i] || 0;
                const x = padding.left + (i / 255) * chartW;
                const y = padding.top + chartH - (val / maxCount) * chartH;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
            ctx.restore();
        });
    }
}

window.HistogramRenderer = HistogramRenderer;
