// Responsive Sidebar Navigation System JavaScript

class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.mainContent = document.getElementById('mainContent');
        this.sidebarOverlay = document.getElementById('sidebarOverlay');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.mobileMenuToggle = document.getElementById('mobileMenuToggle');
        
        this.isCollapsed = false;
        this.isMobile = window.innerWidth < 992;
        this.isInitialized = false;
        
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Set initial state based on screen size
        this.handleResize();
        
        // Set active navigation item
        this.setActiveNavItem();
        
        // Add tooltips for collapsed sidebar
        this.setupTooltips();
        
        this.isInitialized = true;
        console.log('Sidebar initialized successfully');
    }

    setupEventListeners() {
        // Desktop sidebar toggle
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleSidebar();
            });
        }

        // Mobile menu toggle
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMobileSidebar();
            });
        }

        // Overlay click to close mobile sidebar
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => {
                this.closeMobileSidebar();
            });
        }

        // Window resize handler
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });

        // Navigation link clicks
        const navLinks = document.querySelectorAll('.sidebar .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                this.handleNavLinkClick(e, link);
            });
        });

        // Handle navigation state changes
        window.addEventListener('popstate', () => {
            this.setActiveNavItem();
        });
    }

    toggleSidebar() {
        if (this.isMobile) {
            this.toggleMobileSidebar();
            return;
        }

        this.isCollapsed = !this.isCollapsed;
        
        if (this.isCollapsed) {
            this.sidebar.classList.add('collapsed');
            this.mainContent.classList.add('sidebar-collapsed');
        } else {
            this.sidebar.classList.remove('collapsed');
            this.mainContent.classList.remove('sidebar-collapsed');
        }

        // Store preference in localStorage
        localStorage.setItem('sidebarCollapsed', this.isCollapsed);
        
        // Trigger custom event
        this.dispatchEvent('sidebarToggle', { collapsed: this.isCollapsed });
    }

    toggleMobileSidebar() {
        const isOpen = this.sidebar.classList.contains('show');
        
        if (isOpen) {
            this.closeMobileSidebar();
        } else {
            this.openMobileSidebar();
        }
    }

    openMobileSidebar() {
        this.sidebar.classList.add('show');
        this.sidebarOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Focus first navigation item for accessibility
        const firstNavLink = this.sidebar.querySelector('.nav-link');
        if (firstNavLink) {
            setTimeout(() => firstNavLink.focus(), 300);
        }
        
        this.dispatchEvent('mobileSidebarOpen');
    }

    closeMobileSidebar() {
        this.sidebar.classList.remove('show');
        this.sidebarOverlay.classList.remove('active');
        document.body.style.overflow = '';
        
        this.dispatchEvent('mobileSidebarClose');
    }

    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth < 992;

        if (wasMobile !== this.isMobile) {
            // Screen size category changed
            if (this.isMobile) {
                // Switched to mobile
                this.sidebar.classList.remove('collapsed');
                this.mainContent.classList.remove('sidebar-collapsed');
                this.closeMobileSidebar();
            } else {
                // Switched to desktop
                this.sidebar.classList.remove('show');
                this.sidebarOverlay.classList.remove('active');
                document.body.style.overflow = '';
                
                // Restore collapsed state from localStorage
                const savedCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
                if (savedCollapsed) {
                    this.isCollapsed = true;
                    this.sidebar.classList.add('collapsed');
                    this.mainContent.classList.add('sidebar-collapsed');
                }
            }
        }
    }

    setActiveNavItem() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar .nav-link');
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            
            // Check if current path matches the link href
            const linkPath = new URL(link.href).pathname;
            if (currentPath === linkPath || 
                (currentPath.startsWith(linkPath) && linkPath !== '/')) {
                link.classList.add('active');
            }
        });
    }

    setupTooltips() {
        const navLinks = document.querySelectorAll('.sidebar .nav-link');
        
        navLinks.forEach(link => {
            const textElement = link.querySelector('.nav-text');
            if (textElement) {
                link.setAttribute('data-tooltip', textElement.textContent.trim());
            }
        });
    }

    handleKeyboardNavigation(e) {
        // ESC key closes mobile sidebar
        if (e.key === 'Escape' && this.isMobile) {
            this.closeMobileSidebar();
        }

        // Alt + S toggles sidebar
        if (e.altKey && e.key === 's') {
            e.preventDefault();
            this.toggleSidebar();
        }
    }

    handleNavLinkClick(e, link) {
        // Add loading state
        link.classList.add('loading');
        
        // Remove loading state after navigation
        setTimeout(() => {
            link.classList.remove('loading');
        }, 1000);

        // Close mobile sidebar on navigation
        if (this.isMobile) {
            setTimeout(() => {
                this.closeMobileSidebar();
            }, 150);
        }

        // Update active state immediately for better UX
        document.querySelectorAll('.sidebar .nav-link').forEach(l => {
            l.classList.remove('active');
        });
        link.classList.add('active');
    }

    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(`sidebar:${eventName}`, {
            detail: detail,
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    // Public API methods
    collapse() {
        if (!this.isMobile && !this.isCollapsed) {
            this.toggleSidebar();
        }
    }

    expand() {
        if (!this.isMobile && this.isCollapsed) {
            this.toggleSidebar();
        }
    }

    isOpen() {
        return this.isMobile ? this.sidebar.classList.contains('show') : !this.isCollapsed;
    }

    destroy() {
        // Clean up event listeners
        if (this.sidebarToggle) {
            this.sidebarToggle.removeEventListener('click', this.toggleSidebar);
        }
        if (this.mobileMenuToggle) {
            this.mobileMenuToggle.removeEventListener('click', this.toggleMobileSidebar);
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.removeEventListener('click', this.closeMobileSidebar);
        }
        
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('keydown', this.handleKeyboardNavigation);
        
        this.isInitialized = false;
    }
}

// Navigation Enhancement Class
class NavigationEnhancer {
    constructor() {
        this.breadcrumbs = [];
        this.init();
    }

    init() {
        this.generateBreadcrumbs();
        this.enhanceNavigation();
    }

    generateBreadcrumbs() {
        const path = window.location.pathname;
        const segments = path.split('/').filter(segment => segment);
        
        this.breadcrumbs = [
            { name: 'Home', url: '/' }
        ];

        let currentPath = '';
        segments.forEach(segment => {
            currentPath += '/' + segment;
            const name = this.formatSegmentName(segment);
            this.breadcrumbs.push({
                name: name,
                url: currentPath
            });
        });

        this.renderBreadcrumbs();
    }

    formatSegmentName(segment) {
        // Convert URL segments to readable names
        const nameMap = {
            'admin': 'Admin',
            'student': 'Student',
            'manage-students': 'Manage Students',
            'manage-courses': 'Manage Courses',
            'manage-attendance': 'Manage Attendance',
            'manage-schedule': 'Manage Schedule',
            'attendance-history': 'Attendance History',
            'id-card': 'ID Card',
            'dashboard': 'Dashboard'
        };

        return nameMap[segment] || segment.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    renderBreadcrumbs() {
        const breadcrumbContainer = document.querySelector('.breadcrumb-container');
        if (!breadcrumbContainer || this.breadcrumbs.length <= 2) return;

        const breadcrumbHTML = `
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    ${this.breadcrumbs.map((crumb, index) => {
                        const isLast = index === this.breadcrumbs.length - 1;
                        return `
                            <li class="breadcrumb-item ${isLast ? 'active' : ''}">
                                ${isLast ? crumb.name : `<a href="${crumb.url}">${crumb.name}</a>`}
                            </li>
                        `;
                    }).join('')}
                </ol>
            </nav>
        `;

        breadcrumbContainer.innerHTML = breadcrumbHTML;
    }

    enhanceNavigation() {
        // Add keyboard shortcuts info
        this.addKeyboardShortcuts();
        
        // Add navigation history
        this.trackNavigationHistory();
    }

    addKeyboardShortcuts() {
        const shortcuts = [
            { key: 'Alt + S', description: 'Toggle sidebar' },
            { key: 'Esc', description: 'Close mobile sidebar' }
        ];

        // Add shortcuts to help tooltip or modal if exists
        const helpButton = document.querySelector('[data-help="shortcuts"]');
        if (helpButton) {
            const shortcutsList = shortcuts.map(s => `${s.key}: ${s.description}`).join('\n');
            helpButton.setAttribute('title', shortcutsList);
        }
    }

    trackNavigationHistory() {
        // Store navigation history in sessionStorage
        const history = JSON.parse(sessionStorage.getItem('navigationHistory') || '[]');
        const currentPage = {
            url: window.location.pathname,
            title: document.title,
            timestamp: Date.now()
        };

        // Avoid duplicates
        const existingIndex = history.findIndex(item => item.url === currentPage.url);
        if (existingIndex > -1) {
            history.splice(existingIndex, 1);
        }

        history.unshift(currentPage);
        
        // Keep only last 10 pages
        if (history.length > 10) {
            history.splice(10);
        }

        sessionStorage.setItem('navigationHistory', JSON.stringify(history));
    }
}

// Accessibility Enhancements
class AccessibilityEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.enhanceKeyboardNavigation();
        this.addAriaLabels();
        this.setupFocusManagement();
        this.addSkipLinks();
    }

    enhanceKeyboardNavigation() {
        // Ensure all interactive elements are keyboard accessible
        const interactiveElements = document.querySelectorAll('button, a, input, select, textarea');
        
        interactiveElements.forEach(element => {
            if (!element.hasAttribute('tabindex') && element.tabIndex === -1) {
                element.tabIndex = 0;
            }
        });
    }

    addAriaLabels() {
        // Add ARIA labels to navigation elements
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.setAttribute('aria-label', 'Main navigation');
        }

        const navLinks = document.querySelectorAll('.sidebar .nav-link');
        navLinks.forEach(link => {
            const text = link.querySelector('.nav-text');
            if (text && !link.hasAttribute('aria-label')) {
                link.setAttribute('aria-label', text.textContent.trim());
            }
        });

        // Add ARIA expanded states
        const toggleButtons = document.querySelectorAll('[data-bs-toggle]');
        toggleButtons.forEach(button => {
            button.setAttribute('aria-expanded', 'false');
        });
    }

    setupFocusManagement() {
        // Manage focus for better keyboard navigation
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');

        if (sidebar && mainContent) {
            // Focus management for sidebar toggle
            document.addEventListener('sidebar:sidebarToggle', (e) => {
                if (e.detail.collapsed) {
                    // Focus moved to main content when sidebar collapses
                    const firstFocusable = mainContent.querySelector('button, a, input, select, textarea');
                    if (firstFocusable) {
                        firstFocusable.focus();
                    }
                }
            });
        }
    }

    addSkipLinks() {
        // Add skip to main content link
        const skipLink = document.createElement('a');
        skipLink.href = '#mainContent';
        skipLink.className = 'skip-link sr-only sr-only-focusable';
        skipLink.textContent = 'Skip to main content';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            z-index: 1000;
            color: white;
            background: #000;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
        `;

        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });

        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });

        document.body.insertBefore(skipLink, document.body.firstChild);
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we have a sidebar (authenticated users)
    if (document.getElementById('sidebar')) {
        // Initialize sidebar manager
        window.sidebarManager = new SidebarManager();
        
        // Initialize navigation enhancer
        window.navigationEnhancer = new NavigationEnhancer();
        
        // Initialize accessibility enhancer
        window.accessibilityEnhancer = new AccessibilityEnhancer();
        
        // Add custom event listeners for other components
        document.addEventListener('sidebar:sidebarToggle', (e) => {
            console.log('Sidebar toggled:', e.detail);
        });

        document.addEventListener('sidebar:mobileSidebarOpen', () => {
            console.log('Mobile sidebar opened');
        });

        document.addEventListener('sidebar:mobileSidebarClose', () => {
            console.log('Mobile sidebar closed');
        });

        console.log('Sidebar system fully initialized');
    }
});

// Export for global access
window.SidebarManager = SidebarManager;
window.NavigationEnhancer = NavigationEnhancer;
window.AccessibilityEnhancer = AccessibilityEnhancer;