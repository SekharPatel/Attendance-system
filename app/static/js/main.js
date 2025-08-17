// Main JavaScript file for Student Attendance Management System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Add loading state to forms
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loading me-2"></span>Processing...';
            }
        });
    });
});

// Utility functions
function showAlert(message, type = 'info') {
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    const alertContainer = document.createElement('div');
    alertContainer.innerHTML = alertHTML;
    
    const main = document.querySelector('main.container');
    main.insertBefore(alertContainer.firstElementChild, main.firstElementChild);
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatTime(timeString) {
    const time = new Date('2000-01-01 ' + timeString);
    return time.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// NFC Integration Functions
class NFCManager {
    constructor() {
        this.isSupported = 'NDEFReader' in window;
        this.reader = null;
    }

    async initialize() {
        if (!this.isSupported) {
            throw new Error('NFC is not supported on this device');
        }

        this.reader = new NDEFReader();
        await this.reader.scan();
        console.log('NFC scan started');
    }

    onReading(callback) {
        if (this.reader) {
            this.reader.addEventListener('reading', callback);
        }
    }

    async writeNFC(data) {
        if (!this.reader) {
            throw new Error('NFC reader not initialized');
        }

        await this.reader.write(data);
        console.log('NFC data written successfully');
    }
}

// Attendance Management Functions
class AttendanceManager {
    constructor() {
        this.nfcManager = new NFCManager();
        this.currentClassSession = null;
    }

    async initializeNFC() {
        try {
            await this.nfcManager.initialize();
            this.nfcManager.onReading(this.handleNFCReading.bind(this));
            showAlert('NFC reader initialized successfully', 'success');
        } catch (error) {
            console.error('NFC initialization failed:', error);
            showAlert('NFC not supported or permission denied', 'warning');
        }
    }

    async handleNFCReading(event) {
        try {
            const decoder = new TextDecoder();
            const data = decoder.decode(event.message.records[0].data);
            
            // Parse NFC data (expected format: "TEMP_CARD:cardId:studentId")
            if (data.startsWith('TEMP_CARD:')) {
                const parts = data.split(':');
                const tempCardId = parts[1];
                const studentId = parts[2];
                
                await this.markAttendance({
                    temp_card_id: tempCardId,
                    class_session_id: this.currentClassSession
                });
            }
        } catch (error) {
            console.error('Error processing NFC data:', error);
            showAlert('Error reading NFC card', 'danger');
        }
    }

    async markAttendance(data) {
        try {
            const response = await fetch('/api/attendance/mark', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                showAlert(`Attendance marked for ${result.student_name}`, 'success');
                this.refreshAttendanceTable();
            } else {
                showAlert(result.error || 'Failed to mark attendance', 'danger');
            }
        } catch (error) {
            console.error('Error marking attendance:', error);
            showAlert('Network error while marking attendance', 'danger');
        }
    }

    refreshAttendanceTable() {
        // Reload the current page to refresh attendance data
        window.location.reload();
    }

    setCurrentClassSession(sessionId) {
        this.currentClassSession = sessionId;
    }
}

// Data Management Functions
class DataManager {
    async fetchStudents() {
        try {
            const response = await fetch('/api/students');
            if (!response.ok) throw new Error('Failed to fetch students');
            return await response.json();
        } catch (error) {
            console.error('Error fetching students:', error);
            throw error;
        }
    }

    async fetchCourses() {
        try {
            const response = await fetch('/api/courses');
            if (!response.ok) throw new Error('Failed to fetch courses');
            return await response.json();
        } catch (error) {
            console.error('Error fetching courses:', error);
            throw error;
        }
    }

    async createStudent(studentData) {
        try {
            const response = await fetch('/api/students', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(studentData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create student');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating student:', error);
            throw error;
        }
    }

    async createCourse(courseData) {
        try {
            const response = await fetch('/api/courses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(courseData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to create course');
            }

            return await response.json();
        } catch (error) {
            console.error('Error creating course:', error);
            throw error;
        }
    }
}

// Export functions for global use
window.AttendanceManager = AttendanceManager;
window.DataManager = DataManager;
window.NFCManager = NFCManager;
window.showAlert = showAlert;
window.formatDateTime = formatDateTime;
window.formatTime = formatTime;

// Initialize attendance manager on pages that need it
if (document.body.classList.contains('attendance-page')) {
    window.attendanceManager = new AttendanceManager();
}

// Table enhancement functions
function enhanceTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    // Add search functionality
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control mb-3';
    searchInput.placeholder = 'Search...';
    
    table.parentNode.insertBefore(searchInput, table);

    searchInput.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });

    // Add sorting functionality
    const headers = table.querySelectorAll('thead th');
    headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(table, index);
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    const isAscending = table.dataset.sortOrder !== 'asc';
    
    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();
        
        if (isAscending) {
            return aText.localeCompare(bText, undefined, {numeric: true});
        } else {
            return bText.localeCompare(aText, undefined, {numeric: true});
        }
    });
    
    rows.forEach(row => tbody.appendChild(row));
    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
}

// Print functionality
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Print</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    @media print {
                        body { padding: 20px; }
                        .no-print { display: none !important; }
                    }
                </style>
            </head>
            <body>
                ${element.outerHTML}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Export data functionality
function exportToCSV(data, filename) {
    const csvContent = "data:text/csv;charset=utf-8," 
        + data.map(row => row.join(",")).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
