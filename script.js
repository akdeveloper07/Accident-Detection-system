// static/js/script.js

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Premium UI Initializing...');
    
    // Initialize AOS
    AOS.init({
        duration: 1000,
        once: true,
        offset: 50
    });
    
    // Hide loader after content loads
    setTimeout(() => {
        document.getElementById('loader').classList.add('hidden');
    }, 2000);
    
    // Initialize WebSocket
    initWebSocket();
    
    // Initialize Charts
    initCharts();
    
    // Initialize Counters
    initCounters();
    
    // Initialize Event Listeners
    initEventListeners();
    
    // Start updating server time
    updateServerTime();
    setInterval(updateServerTime, 1000);
});

// ===== WEBSOCKET CONNECTION =====
let socket = null;

function initWebSocket() {
    socket = io.connect('http://' + document.domain + ':' + location.port);
    
    socket.on('connect', () => {
        console.log('✅ Connected to server');
        updateConnectionStatus(true);
        showToast('Connected to server', 'success');
    });
    
    socket.on('disconnect', () => {
        console.log('❌ Disconnected from server');
        updateConnectionStatus(false);
        showToast('Lost connection to server', 'error');
    });
    
    socket.on('accident_alert', (data) => {
        console.log('🚨 Accident Alert:', data);
        handleAccidentAlert(data);
    });
    
    socket.on('new_detection', (data) => {
        console.log('🔍 New Detection:', data);
        updateDetectionMetrics(data);
    });
    
    socket.on('stats_update', (data) => {
        console.log('📊 Stats Update:', data);
        updateStats(data);
    });
}

function updateConnectionStatus(connected) {
    const dot = document.querySelector('.connection-dot');
    const text = document.getElementById('connectionText');
    
    if (connected) {
        dot.classList.remove('disconnected');
        dot.classList.add('connected');
        text.textContent = 'Connected to server';
    } else {
        dot.classList.remove('connected');
        dot.classList.add('disconnected');
        text.textContent = 'Disconnected';
    }
}

// ===== PAGE NAVIGATION =====
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
        item.classList.add('active');
        
        // Show corresponding page
        const pageId = item.dataset.page;
        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
        document.getElementById(pageId + '-page').classList.add('active');
        
        // Trigger confetti for dashboard
        if (pageId === 'dashboard') {
            triggerConfetti();
        }
    });
});

// ===== ANIMATED COUNTERS =====
function initCounters() {
    const counters = document.querySelectorAll('.counter');
    
    counters.forEach(counter => {
        const target = parseFloat(counter.dataset.target);
        const decimals = parseInt(counter.dataset.decimals) || 0;
        const duration = 2000;
        const step = target / (duration / 16);
        
        let current = 0;
        const updateCounter = () => {
            current += step;
            if (current < target) {
                counter.textContent = current.toFixed(decimals);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target.toFixed(decimals);
            }
        };
        
        updateCounter();
    });
}

// ===== CHARTS INITIALIZATION =====
let charts = {};

function initCharts() {
    // Severity Distribution Chart
    const ctx1 = document.getElementById('severityChart')?.getContext('2d');
    if (ctx1) {
        charts.severity = new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['Minor', 'Major', 'Critical'],
                datasets: [{
                    data: [12, 8, 4],
                    backgroundColor: ['#f59e0b', '#6366f1', '#ef4444'],
                    borderWidth: 0,
                    borderRadius: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                cutout: '70%',
                animation: {
                    animateRotate: true,
                    animateScale: true
                }
            }
        });
    }
    
    // Time Chart
    const ctx2 = document.getElementById('timeChart')?.getContext('2d');
    if (ctx2) {
        charts.time = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                datasets: [{
                    label: 'Accidents',
                    data: [3, 5, 12, 8, 15, 9],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#64748b'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#64748b'
                        }
                    }
                }
            }
        });
    }
    
    // Pie Chart
    const ctx3 = document.getElementById('pieChart')?.getContext('2d');
    if (ctx3) {
        charts.pie = new Chart(ctx3, {
            type: 'pie',
            data: {
                labels: ['Minor', 'Major', 'Critical'],
                datasets: [{
                    data: [45, 30, 25],
                    backgroundColor: ['#f59e0b', '#6366f1', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#64748b'
                        }
                    }
                }
            }
        });
    }
    
    // Confidence Chart
    const ctx4 = document.getElementById('confidenceChart')?.getContext('2d');
    if (ctx4) {
        charts.confidence = new Chart(ctx4, {
            type: 'bar',
            data: {
                labels: ['80-90%', '90-95%', '95-99%'],
                datasets: [{
                    data: [20, 35, 45],
                    backgroundColor: '#10b981',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#64748b'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#64748b'
                        }
                    }
                }
            }
        });
    }
    
    // Response Time Chart
    const ctx5 = document.getElementById('responseChart')?.getContext('2d');
    if (ctx5) {
        charts.response = new Chart(ctx5, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Response Time (min)',
                    data: [4.2, 3.8, 2.5, 1.8],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#64748b'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#64748b'
                        }
                    }
                }
            }
        });
    }
}

// ===== DETECTION METRICS UPDATE =====
function updateDetectionMetrics(data) {
    // Update accident status
    const statusEl = document.getElementById('accidentStatus');
    const statusBar = document.getElementById('statusBar');
    
    if (data.accident_detected) {
        statusEl.textContent = 'ACCIDENT DETECTED';
        statusEl.style.color = '#ef4444';
        statusBar.style.width = '100%';
        statusBar.style.background = 'linear-gradient(90deg, #ef4444, #f59e0b)';
    } else {
        statusEl.textContent = 'Normal';
        statusEl.style.color = '#10b981';
        statusBar.style.width = '0%';
    }
    
    // Update severity
    const severityEl = document.getElementById('severityLevel');
    if (data.severity) {
        severityEl.textContent = data.severity;
        
        // Update severity dots
        document.querySelectorAll('.severity-dot').forEach(dot => dot.classList.remove('active'));
        const severityLower = data.severity.toLowerCase();
        document.querySelector(`.severity-dot.${severityLower}`)?.classList.add('active');
    }
    
    // Update confidence circle
    const confidence = data.severity_confidence || (data.confidence * 100) || 0;
    const confidenceEl = document.getElementById('confidenceValue');
    const confidencePercent = document.getElementById('confidencePercentage');
    const confidencePath = document.getElementById('confidencePath');
    
    confidenceEl.textContent = confidence.toFixed(1) + '%';
    confidencePercent.textContent = confidence.toFixed(0) + '%';
    
    const circumference = 100;
    const offset = circumference - (confidence / 100) * circumference;
    confidencePath.style.strokeDasharray = `${circumference} ${circumference}`;
    confidencePath.style.strokeDashoffset = offset;
    
    // Update confidence color
    if (confidence >= 85) {
        confidencePath.style.stroke = '#10b981';
    } else if (confidence >= 65) {
        confidencePath.style.stroke = '#f59e0b';
    } else {
        confidencePath.style.stroke = '#ef4444';
    }
    
    // Update vehicle count
    document.getElementById('vehicleCount').textContent = data.vehicle_count || 0;
    
    // Update severity factors
    if (data.severity_factors) {
        document.getElementById('factorOverlap').textContent = 
            (data.severity_factors.overlap || 0).toFixed(0);
        document.getElementById('factorMotion').textContent = 
            (data.severity_factors.motion || 0).toFixed(0);
        document.getElementById('factorDebris').textContent = 
            (data.severity_factors.debris || 0).toFixed(0);
    }
}

// ===== HANDLE ACCIDENT ALERT =====
function handleAccidentAlert(data) {
    // Show toast notification
    showToast(`${data.severity} Accident Detected!`, 'warning');
    
    // Trigger confetti for critical accidents
    if (data.severity === 'CRITICAL') {
        triggerConfetti();
    }
    
    // Play sound based on severity
    playAlertSound(data.severity);
    
    // Add to timeline
    addToTimeline(data);
    
    // Update metrics
    updateDetectionMetrics(data);
}

function addToTimeline(data) {
    const timeline = document.getElementById('alertTimeline');
    if (!timeline) return;
    
    const item = document.createElement('div');
    item.className = 'timeline-item';
    
    const severityLower = data.severity.toLowerCase();
    const time = new Date().toLocaleTimeString();
    
    item.innerHTML = `
        <div class="timeline-icon ${severityLower}">
            <i class="fas ${getSeverityIcon(data.severity)}"></i>
        </div>
        <div class="timeline-content">
            <div class="timeline-title">${data.severity} Accident Detected</div>
            <div class="timeline-time">${time} - Confidence: ${(data.confidence * 100).toFixed(1)}%</div>
        </div>
    `;
    
    timeline.insertBefore(item, timeline.firstChild);
    
    // Limit to 10 items
    if (timeline.children.length > 10) {
        timeline.removeChild(timeline.lastChild);
    }
}

function getSeverityIcon(severity) {
    const icons = {
        'MINOR': 'fa-car',
        'MAJOR': 'fa-truck',
        'CRITICAL': 'fa-bomb'
    };
    return icons[severity] || 'fa-exclamation-triangle';
}

// ===== SIMULATE ACCIDENT =====
async function simulateAccident(severity) {
    try {
        const response = await fetch('/api/simulate/' + severity, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`${severity} accident simulated`, 'success');
            
            // Trigger visual feedback
            const btn = document.querySelector(`.sim-btn.${severity.toLowerCase()}`);
            btn.classList.add('pulse-animation');
            setTimeout(() => btn.classList.remove('pulse-animation'), 1000);
        }
    } catch (error) {
        console.error('Simulation error:', error);
    }
}

// ===== CLEAR HISTORY =====
async function clearHistory() {
    if (!confirm('Clear all alert history?')) return;
    
    try {
        const response = await fetch('/api/clear-history', {
            method: 'POST'
        });
        
        if (response.ok) {
            document.getElementById('alertTimeline').innerHTML = '';
            showToast('History cleared', 'success');
        }
    } catch (error) {
        console.error('Clear history error:', error);
    }
}

// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        warning: 'fa-exclamation-triangle',
        error: 'fa-times-circle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-icon ${type}">
            <i class="fas ${icons[type]}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${type.toUpperCase()}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// ===== PLAY ALERT SOUND =====
function playAlertSound(severity) {
    const audio = new Audio();
    
    // Different sounds for different severities
    const sounds = {
        'MINOR': 'data:audio/wav;base64,UklGRlwAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVQAAACAgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgIAAA',
        'MAJOR': 'data:audio/wav;base64,UklGRlwAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVQAAACAgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgIAAA',
        'CRITICAL': 'data:audio/wav;base64,UklGRlwAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVQAAACAgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgICAf39/f39/f3+AgIAAA'
    };
    
    audio.src = sounds[severity] || sounds['MAJOR'];
    audio.play().catch(() => {}); // Ignore autoplay errors
}

// ===== CONFETTI EFFECT =====
function triggerConfetti() {
    confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#6366f1', '#8b5cf6', '#ec4899']
    });
    
    // Add confetti elements
    for (let i = 0; i < 50; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.background = `hsl(${Math.random() * 360}, 70%, 50%)`;
            confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 3000);
        }, i * 50);
    }
}

// ===== SERVER TIME UPDATE =====
function updateServerTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('serverTime').textContent = `Server Time: ${timeString}`;
}

// ===== STATS UPDATE =====
function updateStats(data) {
    // Update counters
    document.querySelector('.counter[data-target="24"]').textContent = data.accidents_detected || 24;
    
    // Update charts if needed
    if (charts.severity && data.severity_counts) {
        charts.severity.data.datasets[0].data = [
            data.severity_counts.MINOR || 12,
            data.severity_counts.MAJOR || 8,
            data.severity_counts.CRITICAL || 4
        ];
        charts.severity.update();
    }
}

// ===== EVENT LISTENERS =====
function initEventListeners() {
    // Video controls
    document.getElementById('captureBtn')?.addEventListener('click', () => {
        showToast('Screenshot captured', 'success');
    });
    
    document.getElementById('recordBtn')?.addEventListener('click', (btn) => {
        btn.classList.toggle('active');
        showToast(btn.classList.contains('active') ? 'Recording started' : 'Recording stopped', 'info');
    });
    
    document.getElementById('fullscreenBtn')?.addEventListener('click', () => {
        const container = document.getElementById('videoContainer');
        if (container.requestFullscreen) {
            container.requestFullscreen();
        }
    });
    
    document.getElementById('startCameraBtn')?.addEventListener('click', () => {
        showToast('Camera starting...', 'info');
    });
    
    document.getElementById('uploadVideoBtn')?.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'video/*';
        input.onchange = () => showToast('Video uploaded', 'success');
        input.click();
    });
    
    // Search and filter
    document.querySelector('.search-input')?.addEventListener('input', (e) => {
        console.log('Searching:', e.target.value);
    });
    
    document.querySelector('.filter-select')?.addEventListener('change', (e) => {
        console.log('Filter:', e.target.value);
    });
    
    // Settings toggles
    document.querySelectorAll('.switch input').forEach(toggle => {
        toggle.addEventListener('change', (e) => {
            showToast(`Setting ${e.target.checked ? 'enabled' : 'disabled'}`, 'success');
        });
    });
}

// ===== ERROR HANDLING =====
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Error:', msg);
    showToast('An error occurred', 'error');
    return false;
};

// ===== CLEANUP =====
window.onbeforeunload = () => {
    if (socket) {
        socket.disconnect();
    }
};
