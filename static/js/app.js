/**
 * Violet Lens — Main Application Controller
 * Handles navigation, modal lifecycle, responsive mobile toggle, and toast notifications.
 */

class VioletLensApp {
    constructor() {
        this.init();
    }

    init() {
        // Instantiate component controllers
        window.uploadController = new window.UploadController();
        window.AnalysisController = new window.AnalysisController();

        this._bindNavElements();
        this._bindModals();
        this._bindMobileToggle();
        this._bindResize();
    }

    _bindNavElements() {
        const workspaceBtn = document.getElementById('navWorkspaceBtn');
        const methodologyBtn = document.getElementById('navMethodologyBtn');
        const aboutBtn = document.getElementById('navAboutBtn');

        if (workspaceBtn) {
            workspaceBtn.addEventListener('click', () => {
                this._setActiveNav(workspaceBtn);
                window.scrollTo({ top: 0, behavior: 'smooth' });
                this._closeMobileSidebar();
            });
        }

        if (methodologyBtn) {
            methodologyBtn.addEventListener('click', () => {
                this.openModal('methodologyModal');
                this._closeMobileSidebar();
            });
        }

        if (aboutBtn) {
            aboutBtn.addEventListener('click', () => {
                this.openModal('aboutModal');
                this._closeMobileSidebar();
            });
        }
    }

    _setActiveNav(activeBtn) {
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
            btn.classList.remove('active');
        });
        if (activeBtn) activeBtn.classList.add('active');
    }

    _bindModals() {
        const modals = ['methodologyModal', 'aboutModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (!modal) return;

            // Close on backdrop click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modalId);
                }
            });
        });

        // Close buttons
        const closeMethodologyBtn = document.getElementById('closeMethodologyModalBtn');
        const dismissMethodologyBtn = document.getElementById('dismissMethodologyBtn');
        if (closeMethodologyBtn) closeMethodologyBtn.addEventListener('click', () => this.closeModal('methodologyModal'));
        if (dismissMethodologyBtn) dismissMethodologyBtn.addEventListener('click', () => this.closeModal('methodologyModal'));

        const closeAboutBtn = document.getElementById('closeAboutModalBtn');
        const dismissAboutBtn = document.getElementById('dismissAboutBtn');
        if (closeAboutBtn) closeAboutBtn.addEventListener('click', () => this.closeModal('aboutModal'));
        if (dismissAboutBtn) dismissAboutBtn.addEventListener('click', () => this.closeModal('aboutModal'));

        // ESC key listener
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modals.forEach(id => this.closeModal(id));
            }
        });
    }

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    _bindMobileToggle() {
        const toggleBtn = document.getElementById('mobileMenuToggle');
        const sidebar = document.getElementById('appSidebar');

        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                sidebar.classList.toggle('mobile-open');
            });

            // Close sidebar when clicking outside on mobile
            document.addEventListener('click', (e) => {
                if (sidebar.classList.contains('mobile-open') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
                    sidebar.classList.remove('mobile-open');
                }
            });
        }
    }

    _closeMobileSidebar() {
        const sidebar = document.getElementById('appSidebar');
        if (sidebar) sidebar.classList.remove('mobile-open');
    }

    _bindResize() {
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                if (window.AnalysisController && window.AnalysisController.histogramRenderer) {
                    window.AnalysisController.histogramRenderer.render();
                }
            }, 150);
        });
    }

    showToast(message, duration = 3000) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <span>${message}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.25s ease';
            setTimeout(() => toast.remove(), 250);
        }, duration);
    }
}

// Bootstrap once DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VioletLensApp();
});
