// AquaPulse - Modals JavaScript
class ModalManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupSensorModals();
        this.setupAgentOptimization();
        this.setupMetricClicks();
    }

    setupSensorModals() {
        // Make sensor markers clickable to show details
        document.addEventListener('click', (e) => {
            if (e.target.closest('.sensor-marker') || e.target.closest('.metric-card')) {
                const sensorId = e.target.dataset.sensorId || e.target.closest('[data-sensor-id]')?.dataset.sensorId;
                if (sensorId) {
                    this.showSensorDetails(sensorId);
                }
            }
        });
    }

    setupMetricClicks() {
        // Make metric cards clickable
        document.querySelectorAll('.metric-card').forEach(card => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                const metricType = card.dataset.metric || 'general';
                this.showMetricDetails(metricType);
            });
        });
    }

    showSensorDetails(sensorId) {
        const sensorData = this.getSensorData(sensorId);
        const modal = document.getElementById('sensorModal');
        const title = document.getElementById('sensorModalTitle');
        const body = document.getElementById('sensorModalBody');

        title.textContent = `${sensorData.location} - Sensor ${sensorData.id}`;
        
        body.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6 class="text-primary">Current Readings</h6>
                    <div class="sensor-details">
                        <div class="detail-item">
                            <span class="label">Pollution Level:</span>
                            <span class="value ${sensorData.pollution_level > 8 ? 'text-danger' : sensorData.pollution_level > 5 ? 'text-warning' : 'text-success'}">${sensorData.pollution_level}/10</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Microplastics:</span>
                            <span class="value">${sensorData.microplastics?.toLocaleString() || 'N/A'} particles/m³</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Temperature:</span>
                            <span class="value">${sensorData.temperature || 'N/A'}°C</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Turbidity:</span>
                            <span class="value">${sensorData.turbidity || 'N/A'} NTU</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">Status:</span>
                            <span class="badge ${sensorData.status === 'warning' ? 'bg-warning' : 'bg-success'}">${sensorData.status}</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6 class="text-primary">AI Analysis</h6>
                    <div class="ai-insights">
                        <p><strong>Risk Assessment:</strong> ${this.generateRiskAssessment(sensorData)}</p>
                        <p><strong>Trend:</strong> ${this.generateTrendAnalysis(sensorData)}</p>
                        <p><strong>Recommendation:</strong> ${this.generateRecommendation(sensorData)}</p>
                    </div>
                    <h6 class="text-primary mt-3">Historical Data</h6>
                    <div class="mini-chart">
                        <canvas id="sensorChart" width="300" height="150"></canvas>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <h6 class="text-primary">Actions</h6>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-primary" onclick="modalManager.deployCleanupUnit('${sensorId}')">
                            <i class="fas fa-robot"></i> Deploy Cleanup Unit
                        </button>
                        <button class="btn btn-sm btn-info" onclick="modalManager.showAIAgentModal()">
                            <i class="fas fa-brain"></i> AI Agent Optimization
                        </button>
                        <button class="btn btn-sm btn-success" onclick="modalManager.generateReport('${sensorId}')">
                            <i class="fas fa-file-alt"></i> Generate Report
                        </button>
                    </div>
                </div>
            </div>
        `;

        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Draw mini chart
        setTimeout(() => this.drawSensorChart(sensorData), 100);
    }

    showMetricDetails(metricType) {
        const modal = document.getElementById('sensorModal');
        const title = document.getElementById('sensorModalTitle');
        const body = document.getElementById('sensorModalBody');

        title.textContent = `${metricType.charAt(0).toUpperCase() + metricType.slice(1)} Metrics Details`;
        
        body.innerHTML = `
            <div class="row">
                <div class="col-12">
                    <h6 class="text-primary">Detailed Analytics</h6>
                    <div class="metrics-breakdown" id="metrics-breakdown-area">
                        ${this.generateMetricsBreakdown(metricType)}
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <button class="btn btn-primary" id="launch-ai-optimization-btn">
                        <i class="fas fa-robot"></i> Launch AI Agent Optimization
                    </button>
                </div>
            </div>
        `;

        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Add animation logic for the button
        setTimeout(() => {
            const launchBtn = document.getElementById('launch-ai-optimization-btn');
            if (launchBtn) {
                launchBtn.onclick = () => {
                    const breakdown = document.getElementById('metrics-breakdown-area');
                    if (breakdown) {
                        // Save original content
                        const original = breakdown.innerHTML;
                        // Animation steps
                        const steps = [
                            'Optimizing using AWS Bedrock...',
                            'Solving with multiple agents...',
                            'Coordinating AI resources...',
                            'Finalizing optimization...'
                        ];
                        let idx = 0;
                        breakdown.innerHTML = `<div class='text-center py-5'><span class='spinner-border text-primary mb-3' style='width:2.5rem;height:2.5rem;'></span><div id='ai-optimization-anim-text' class='fw-bold mt-3'>${steps[0]}</div></div>`;
                        const animText = document.getElementById('ai-optimization-anim-text');
                        const interval = setInterval(() => {
                            idx++;
                            if (idx < steps.length && animText) animText.textContent = steps[idx];
                        }, 900);
                        setTimeout(() => {
                            clearInterval(interval);
                            breakdown.innerHTML = original;
                            // Now open the AI Agent modal
                            setTimeout(() => this.showAIAgentModal(), 300);
                        }, 3200 + Math.random() * 800);
                    }
                };
            }
        }, 200);
    }

    showAIAgentModal() {
        const modal = document.getElementById('aiAgentModal');
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        // Insert metrics summary and chart container if not present
        setTimeout(() => {
            let metricsSection = document.getElementById('optimization-metrics-section');
            if (!metricsSection) {
                const row = document.createElement('div');
                row.className = 'row mt-4';
                row.id = 'optimization-metrics-section';
                row.innerHTML = `
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-body">
                                <h6 class="card-title text-primary">Live Optimization Metrics</h6>
                                <ul class="list-unstyled mb-0" id="live-metrics-list">
                                    <li><strong>Efficiency:</strong> <span id="live-efficiency">62%</span></li>
                                    <li><strong>Response Time:</strong> <span id="live-response">8.2s</span></li>
                                    <li><strong>Resource Usage:</strong> <span id="live-resource">78%</span></li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-body">
                                <h6 class="card-title text-primary">Optimization Progress Chart</h6>
                                <canvas id="optimizationChart" height="180"></canvas>
                            </div>
                        </div>
                    </div>
                `;
                // Insert after optimization log
                const logRow = modal.querySelector('#optimization-log').closest('.col-md-6').parentElement;
                logRow.parentNode.insertBefore(row, logRow.nextSibling);
            }
            this.initOptimizationChart();
        }, 1200);
        // Start the demo workflow
        setTimeout(() => this.startAgentWorkflow(), 1000);
    }

    initOptimizationChart() {
        if (this.optimizationChart) return;
        const ctx = document.getElementById('optimizationChart');
        if (!ctx) return;
        this.optimizationChartData = {
            labels: ['Start'],
            efficiency: [62],
            response: [8.2],
            resource: [78]
        };
        this.optimizationChart = new window.Chart(ctx, {
            type: 'line',
            data: {
                labels: this.optimizationChartData.labels,
                datasets: [
                    { label: 'Efficiency (%)', data: this.optimizationChartData.efficiency, borderColor: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', fill: false },
                    { label: 'Response Time (s)', data: this.optimizationChartData.response, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: false },
                    { label: 'Resource Usage (%)', data: this.optimizationChartData.resource, borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,0.1)', fill: false }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: true } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });
    }

    updateOptimizationMetrics(step) {
        // Fetch real metrics from backend (placeholder: fetch from /api/optimization-metrics or similar)
        fetch('/api/optimization-metrics?step=' + step)
            .then(response => response.json())
            .then(m => {
                document.getElementById('live-efficiency').textContent = m.efficiency + '%';
                document.getElementById('live-response').textContent = m.response + 's';
                document.getElementById('live-resource').textContent = m.resource + '%';
                if (this.optimizationChart) {
                    this.optimizationChartData.labels.push('Step ' + (step + 1));
                    this.optimizationChartData.efficiency.push(m.efficiency);
                    this.optimizationChartData.response.push(m.response);
                    this.optimizationChartData.resource.push(m.resource);
                    this.optimizationChart.update();
                }
            })
            .catch(() => {/* If no data, do not update */});
    }

    setupAgentOptimization() {
        // Initialize agent optimization system
        this.agentStates = {
            detection: 'active',
            prediction: 'active', 
            cleanup: 'active',
            coordination: 'active'
        };
        
        this.optimizationLogs = [];
        this.workflowStep = 3; // Start at step 3 (processing)
    }

    startAgentWorkflow() {
        // Simulate complex multi-step agent coordination
        this.addOptimizationLog('INFO', 'Multi-agent coordination initiated');
        this.addOptimizationLog('SUCCESS', 'Detection agents analyzing satellite imagery');
        
        // Progress through workflow steps
        setTimeout(() => this.progressWorkflow(), 2000);
        setTimeout(() => this.simulateAgentInteractions(), 1000);
    }

    progressWorkflow() {
        const steps = ['step-3', 'step-4', 'step-5'];
        let currentIndex = 0;

        const progressInterval = setInterval(() => {
            if (currentIndex < steps.length) {
                const step = document.getElementById(steps[currentIndex]);
                if (step) {
                    step.classList.remove('pending');
                    step.classList.add('processing');
                    
                    const progressBar = step.querySelector('.progress-bar');
                    this.animateProgress(progressBar, () => {
                        step.classList.remove('processing');
                        step.classList.add('active');
                        progressBar.classList.remove('bg-warning', 'bg-info');
                        progressBar.classList.add('bg-success');
                        progressBar.style.width = '100%';
                    });
                }
                currentIndex++;
            } else {
                clearInterval(progressInterval);
                this.addOptimizationLog('SUCCESS', 'Multi-step coordination complete');
                this.addOptimizationLog('SUCCESS', 'Autonomous cleanup units deployed');
            }
        }, 3000);
    }

    animateProgress(progressBar, callback) {
        let width = parseInt(progressBar.style.width) || 0;
        const interval = setInterval(() => {
            width += 5;
            progressBar.style.width = width + '%';
            if (width >= 100) {
                clearInterval(interval);
                if (callback) callback();
            }
        }, 100);
    }

    simulateAgentInteractions() {
        // Fetch real agent log/metrics from backend (placeholder: fetch from /api/agent-logs)
        fetch('/api/agent-logs')
            .then(response => response.json())
            .then(logs => {
                logs.forEach((log, i) => {
                    setTimeout(() => {
                        this.addOptimizationLog(log.level, log.message);
                        if (typeof log.metricsStep !== 'undefined') {
                            this.updateOptimizationMetrics(log.metricsStep);
                        }
                    }, log.delay || (i * 1000));
                });
            });
    }

    addOptimizationLog(level, message) {
        const console = document.getElementById('optimization-log');
        if (!console) return;

        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="timestamp">${timestamp}</span>
            <span class="level ${level.toLowerCase()}">${level}</span>
            <span class="message">${message}</span>
        `;

        console.appendChild(logEntry);
        console.scrollTop = console.scrollHeight;

        // Keep only last 10 entries
        const entries = console.querySelectorAll('.log-entry');
        if (entries.length > 10) {
            entries[0].remove();
        }
    }

    getSensorData(sensorId) {
        // Get sensor data from global data only
        const sensorDataElement = document.getElementById('sensor-data');
        let sensors = [];
        try {
            sensors = JSON.parse(sensorDataElement.textContent);
        } catch (e) {
            // No fallback, just return null
            return null;
        }
        return sensors.find(s => s.id === sensorId) || null;
    }

    generateRiskAssessment(sensor) {
        if (sensor.pollution_level > 8) return 'Critical - Immediate intervention required';
        if (sensor.pollution_level > 6) return 'High - Monitoring and cleanup recommended';
        if (sensor.pollution_level > 4) return 'Moderate - Continued observation needed';
        return 'Low - Normal pollution levels detected';
    }

    generateTrendAnalysis(sensor) {
        // Optionally fetch trend from backend if available
        return sensor && sensor.trend ? sensor.trend : 'No trend data available';
    }

    generateRecommendation(sensor) {
        // Only use real data if available
        return sensor && sensor.recommendation ? sensor.recommendation : 'No recommendation data available.';
    }

    generateMetricsBreakdown(metricType) {
        // Only use real data if available, otherwise show message
        return `<div class="metric-detail">No real metric breakdown data available.</div>`;
    }

    drawSensorChart(sensor) {
        const canvas = document.getElementById('sensorChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const data = this.generateHistoricalData(sensor);
        if (!data.length) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = '14px Arial';
            ctx.fillStyle = '#888';
            ctx.fillText('No historical data', 10, canvas.height / 2);
            return;
        }
        // Simple line chart
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = sensor.pollution_level > 7 ? '#ff5722' : '#1E88E5';
        ctx.lineWidth = 2;
        ctx.beginPath();
        data.forEach((point, index) => {
            const x = (index / (data.length - 1)) * canvas.width;
            const y = canvas.height - (point / 10) * canvas.height;
            if (index === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
    }

    generateHistoricalData(sensor) {
        // Use real historical data if available
        if (sensor && sensor.historical_data && Array.isArray(sensor.historical_data)) {
            return sensor.historical_data;
        }
        // No fallback, return empty array
        return [];
    }

    deployCleanupUnit(sensorId) {
        this.addOptimizationLog('INFO', `Deploying cleanup unit to ${sensorId}`);
        // TODO: Implement real backend call to deploy cleanup unit
        this.addOptimizationLog('SUCCESS', 'Autonomous unit dispatched (real backend call needed)');
        // Close sensor modal and show agent modal
        const sensorModal = bootstrap.Modal.getInstance(document.getElementById('sensorModal'));
        if (sensorModal) sensorModal.hide();
        setTimeout(() => this.showAIAgentModal(), 500);
    }

    generateReport(sensorId) {
        this.addOptimizationLog('INFO', `Generating comprehensive report for ${sensorId}`);
        // TODO: Implement real backend call to generate report
        setTimeout(() => {
            this.addOptimizationLog('SUCCESS', 'Report generated and transmitted (real backend call needed)');
            alert('Pollution report generated and sent to environmental authorities (real backend call needed)');
        }, 1500);
    }
}

// Global function for button onclick
function runAgentOptimization() {
    if (window.modalManager) {
        window.modalManager.addOptimizationLog('INFO', 'Manual optimization triggered');
        window.modalManager.startAgentWorkflow();
    }
}

// Initialize modal manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.modalManager = new ModalManager();
});