/**
 * Dashboard JavaScript functionality
 * Handles chart initialization and dashboard interactions
 */

class DashboardManager {
    constructor(dashboardData) {
        this.data = dashboardData;
        this.charts = {};
        this.init();
    }

    init() {
        this.initializeTodayAttendanceChart();
        this.initializeAttendanceTrendChart();
        this.initializeProgressCircle();
        this.setupEventListeners();
    }

    /**
     * Initialize Today's Attendance Donut Chart
     */
    initializeTodayAttendanceChart() {
        const ctx = document.getElementById('todayAttendanceChart');
        if (!ctx) return;

        this.charts.todayAttendance = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent'],
                datasets: [{
                    data: [this.data.today_attendance.present, this.data.today_attendance.absent],
                    backgroundColor: ['#28a745', '#dc3545'],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed * 100) / total).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 1000
                }
            }
        });
    }

    /**
     * Initialize Attendance Trend Line Chart
     */
    initializeAttendanceTrendChart() {
        const ctx = document.getElementById('attendanceTrendChart');
        if (!ctx) return;

        this.charts.attendanceTrend = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: this.data.trend_labels,
                datasets: [{
                    label: 'Attendance Rate (%)',
                    data: this.data.trend_data,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#007bff',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#007bff',
                        borderWidth: 1,
                        callbacks: {
                            label: (context) => `Attendance: ${context.parsed.y}%`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: (value) => `${value}%`
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 1500,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    /**
     * Initialize Progress Circle Animation
     */
    initializeProgressCircle() {
        const progressCircle = document.querySelector('.progress-circle');
        if (!progressCircle) return;

        const percentage = parseInt(progressCircle.dataset.percentage) || this.data.attendance_percentage;
        
        // Create SVG circle for progress
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '120');
        svg.setAttribute('height', '120');
        svg.style.position = 'absolute';
        svg.style.top = '0';
        svg.style.left = '50%';
        svg.style.transform = 'translateX(-50%)';
        
        // Background circle
        const bgCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        bgCircle.setAttribute('cx', '60');
        bgCircle.setAttribute('cy', '60');
        bgCircle.setAttribute('r', '50');
        bgCircle.setAttribute('fill', 'none');
        bgCircle.setAttribute('stroke', '#e9ecef');
        bgCircle.setAttribute('stroke-width', '8');
        
        // Progress circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', '60');
        circle.setAttribute('cy', '60');
        circle.setAttribute('r', '50');
        circle.setAttribute('fill', 'none');
        circle.setAttribute('stroke', '#28a745');
        circle.setAttribute('stroke-width', '8');
        circle.setAttribute('stroke-linecap', 'round');
        circle.setAttribute('stroke-dasharray', '314');
        circle.setAttribute('stroke-dashoffset', '314');
        circle.style.transform = 'rotate(-90deg)';
        circle.style.transformOrigin = '60px 60px';
        circle.style.transition = 'stroke-dashoffset 1.5s ease-in-out';
        
        svg.appendChild(bgCircle);
        svg.appendChild(circle);
        progressCircle.appendChild(svg);
        
        // Animate the circle
        setTimeout(() => {
            const offset = 314 - (314 * percentage / 100);
            circle.style.strokeDashoffset = offset;
        }, 200);

        // Animate the percentage number
        this.animateNumber(progressCircle.querySelector('.progress-percentage'), 0, percentage, 1500);
    }

    /**
     * Animate number counting up
     */
    animateNumber(element, start, end, duration) {
        if (!element) return;

        const startTime = performance.now();
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const current = Math.floor(start + (end - start) * progress);
            
            element.textContent = `${current}%`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Refresh dashboard button
        const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
        if (refreshBtn) {
            refreshBtn.onclick = (e) => {
                e.preventDefault();
                this.refreshDashboard();
            };
        }

        // Trend period change handlers
        document.querySelectorAll('input[name="trendPeriod"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateTrendPeriod(e.target.value);
            });
        });

        // Card hover effects
        document.querySelectorAll('.dashboard-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-2px)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });
    }

    /**
     * Refresh dashboard data
     */
    refreshDashboard() {
        // Show loading state
        this.showLoadingState();
        
        // In a real implementation, this would fetch new data from the server
        setTimeout(() => {
            location.reload();
        }, 500);
    }

    /**
     * Update trend period
     */
    updateTrendPeriod(period) {
        console.log(`Updating trend period to: ${period} days`);
        // In a real implementation, this would fetch new trend data
        // For now, we'll just log the change
    }

    /**
     * Show loading state for charts
     */
    showLoadingState() {
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {
            const canvas = container.querySelector('canvas');
            if (canvas) {
                canvas.style.opacity = '0.5';
            }
        });
    }

    /**
     * Destroy all charts (useful for cleanup)
     */
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Global functions for backward compatibility
function refreshDashboard() {
    if (window.dashboardManager) {
        window.dashboardManager.refreshDashboard();
    } else {
        location.reload();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the dashboard page and have dashboard data
    if (typeof dashboardData !== 'undefined' && document.getElementById('todayAttendanceChart')) {
        window.dashboardManager = new DashboardManager(dashboardData);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
}