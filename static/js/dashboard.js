// AquaPulse - Dashboard JavaScript (Harmful Algae Bloom Edition)

class AquaPulseDashboard {
    constructor() {
        this.refreshInterval = null;
        this.charts = {};
        this.lastUpdate = new Date();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoRefresh();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Refresh button
        window.refreshData = () => this.refreshAllData();
        
        // Voice mode toggle
        window.toggleVoiceMode = () => this.toggleVoicePanel();
        
        // Map layer toggle
        window.toggleMapLayer = () => this.toggleMapLayer();
        
        // Analysis audio playback
        window.playAnalysis = () => this.playAnalysisAudio();
        
        // Image analysis
        window.analyzeUploadedImage = (input) => this.analyzeImage(input);

        // Chat Support Tab: Add event listeners for chat input and send button
        document.addEventListener('DOMContentLoaded', () => {
            const chatInput = document.getElementById('chat-input');
            const sendChatBtn = document.getElementById('send-chat-btn');
            if (chatInput) {
                chatInput.addEventListener('keypress', (event) => {
                    if (event.key === 'Enter') {
                        window.aquaPulseDashboard.sendChatMessage();
                    }
                });
            }
            if (sendChatBtn) {
                sendChatBtn.addEventListener('click', () => {
                    window.aquaPulseDashboard.sendChatMessage();
                });
            }
        });
    }

    loadInitialData() {
        try {
            // Load data from template
            const sensorData = JSON.parse(document.getElementById('sensor-data').textContent);
            const predictionData = JSON.parse(document.getElementById('prediction-data').textContent);
            const cleanupData = JSON.parse(document.getElementById('cleanup-data').textContent);

            this.updatePredictionChart(predictionData);
            this.updateLastUpdateTime();
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    initializeCharts() {
        this.initPredictionChart();
    }

    initPredictionChart() {
        const ctx = document.getElementById('prediction-chart');
        if (!ctx) return;

        this.charts.prediction = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Pacific', 'Atlantic', 'Mediterranean', 'Indian', 'Arctic'],
                datasets: [{
                    label: 'Current Level',
                    data: [],
                    borderColor: '#1E88E5',
                    backgroundColor: 'rgba(30, 136, 229, 0.1)',
                    tension: 0.4
                }, {
                    label: '7-Day Prediction',
                    data: [],
                    borderColor: '#FF5722',
                    backgroundColor: 'rgba(255, 87, 34, 0.1)',
                    borderDash: [5, 5],
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                size: 11
                            },
                            color: '#263238'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            color: '#263238',
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            color: '#E0E0E0'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#263238',
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            color: '#E0E0E0'
                        }
                    }
                }
            }
        });
    }

    updatePredictionChart(predictionData) {
        if (!this.charts.prediction || !predictionData) return;

        const currentLevels = predictionData.map(p => p.current_level);
        const predictions = predictionData.map(p => p.predicted_7days);

        this.charts.prediction.data.datasets[0].data = currentLevels;
        this.charts.prediction.data.datasets[1].data = predictions;
        this.charts.prediction.update();
    }

    async refreshAllData() {
        try {
            this.showLoading(true);

            // Fetch fresh data from the server
            const response = await fetch('/dashboard-data');
            const data = await response.json();

            // Update charts
            this.updatePredictionChart(data.predictions);

            // Update metrics
            this.updateMetrics(data);

            // Update AI analysis
            this.updateAIAnalysis();

            // Update map if available
            if (window.pollutionMap) {
                window.pollutionMap.updateSensorData(data.sensors);
            }

            this.updateLastUpdateTime();
            this.showRefreshSuccess();

        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showRefreshError();
        } finally {
            this.showLoading(false);
        }
    }

    updateMetrics(data) {
        // Update sensor count
        const activeSensors = data.sensors.length;
        this.updateMetricValue(0, activeSensors);

        // Update high pollution count
        const highPollution = data.sensors.filter(s => s.status === 'warning').length;
        this.updateMetricValue(1, highPollution);

        // Update active missions
        this.updateMetricValue(2, data.cleanup.active_missions);

        // Update waste collected
        this.updateMetricValue(3, data.cleanup.waste_collected_today);
    }

    updateMetricValue(index, value) {
        const metricCards = document.querySelectorAll('.metric-value');
        if (metricCards[index]) {
            metricCards[index].textContent = value;
        }
    }

    async updateAIAnalysis() {
        try {
            const response = await fetch('/api/ai-analysis');
            const data = await response.json();
            
            const analysisElement = document.getElementById('ai-analysis');
            if (analysisElement) {
                // Replace any old terminology in the AI response for display
                let html = data.html || data.analysis || '';
                html = html.replace(/Pollution Levels/g, 'Algae Bloom Levels')
                           .replace(/Microplastics Concentration/g, 'Microalgae Concentration')
                           .replace(/particles/g, 'cells/L')
                           .replace(/pollution level/g, 'algae bloom level')
                           .replace(/Pollution/g, 'Algae Bloom')
                           .replace(/pollution/g, 'algae bloom');
                analysisElement.innerHTML = html;
            }
        } catch (error) {
            console.error('Error updating AI analysis:', error);
        }
    }

    async playAnalysisAudio() {
        try {
            const analysisElement = document.getElementById('ai-analysis');
            const analysisText = analysisElement ? analysisElement.textContent || analysisElement.innerText : '';
            
            const response = await fetch('/api/synthesize-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: analysisText,
                    voice_id: 'Joanna'
                })
            });

            const data = await response.json();
            
            if (data.audio) {
                // Convert base64 to audio blob and play
                const audioData = atob(data.audio);
                const audioArray = new Uint8Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    audioArray[i] = audioData.charCodeAt(i);
                }
                
                const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                
                audio.play().catch(error => {
                    console.error('Error playing audio:', error);
                });
            }
        } catch (error) {
            console.error('Error playing analysis audio:', error);
        }
    }

    async analyzeImage(input) {
        if (!input.files || !input.files[0]) return;

        const file = input.files[0];
        const formData = new FormData();
        formData.append('image', file);

        try {
            const response = await fetch('/api/analyze-image', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            const resultDiv = document.getElementById('image-analysis-result');
            if (data.labels && data.labels.length > 0) {
                let html = '<div class="alert alert-info mt-2"><strong>Detected:</strong><ul class="mb-0 mt-1">';
                data.labels.forEach(label => {
                    html += `<li>${label.name} (${label.confidence.toFixed(1)}% confidence)</li>`;
                });
                html += '</ul></div>';
                resultDiv.innerHTML = html;
            } else {
                resultDiv.innerHTML = '<div class="alert alert-warning mt-2">No algae bloom detected in image.</div>';
            }
        } catch (error) {
            console.error('Error analyzing image:', error);
            document.getElementById('image-analysis-result').innerHTML = 
                '<div class="alert alert-danger mt-2">Error analyzing image. Please try again.</div>';
        }
    }

    toggleVoicePanel() {
        const voicePanel = document.getElementById('voice-panel');
        if (voicePanel.style.display === 'none') {
            voicePanel.style.display = 'block';
        } else {
            voicePanel.style.display = 'none';
        }
    }

    toggleMapLayer() {
        if (window.pollutionMap) {
            window.pollutionMap.toggleLayer();
        }
    }

    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.refreshAllData();
        }, 30000);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    updateLastUpdateTime() {
        this.lastUpdate = new Date();
        const timeElement = document.getElementById('last-update');
        if (timeElement) {
            timeElement.textContent = this.lastUpdate.toLocaleTimeString();
        }
    }

    showLoading(show) {
        const dashboard = document.querySelector('.dashboard-grid');
        if (dashboard) {
            if (show) {
                dashboard.classList.add('loading');
            } else {
                dashboard.classList.remove('loading');
            }
        }
    }

    showRefreshSuccess() {
        this.showToast('Data refreshed successfully', 'success');
    }

    showRefreshError() {
        this.showToast('Error refreshing data', 'error');
    }

    showToast(message, type) {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    // Enhanced AWS Services Functions
    async createIoTThing() {
        try {
            const thingName = `pollution-sensor-${Date.now()}`;
            const response = await fetch('/api/create-iot-thing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thing_name: thingName })
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast(`IoT Thing created: ${thingName}`, 'success');
            } else {
                this.showToast('Failed to create IoT Thing', 'error');
            }
        } catch (error) {
            console.error('Error creating IoT Thing:', error);
            this.showToast('Error creating IoT Thing', 'error');
        }
    }

    async publishIoTMessage() {
        try {
            const message = {
                pollution_level: Math.floor(Math.random() * 10) + 1,
                location: 'Pacific Ocean',
                timestamp: new Date().toISOString()
            };
            
            const response = await fetch('/api/publish-iot-message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    thing_name: 'pollution-sensor-001',
                    topic: 'pollution/data',
                    message: message
                })
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast('IoT message published successfully', 'success');
            } else {
                this.showToast('Failed to publish IoT message', 'error');
            }
        } catch (error) {
            console.error('Error publishing IoT message:', error);
            this.showToast('Error publishing IoT message', 'error');
        }
    }

    async showIoTStatus() {
        try {
            const response = await fetch('/api/iot-sensors');
            const sensors = await response.json();
            this.showToast(`Found ${sensors.length} IoT sensors`, 'success');
        } catch (error) {
            console.error('Error getting IoT status:', error);
            this.showToast('Error getting IoT status', 'error');
        }
    }

    async createLambdaFunction(functionType) {
        try {
            const functionName = `pollution-${functionType}-${Date.now()}`;
            const response = await fetch('/api/create-lambda-function', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    function_name: functionName,
                    function_type: functionType
                })
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast(`Lambda function created: ${functionName}`, 'success');
            } else {
                this.showToast('Failed to create Lambda function', 'error');
            }
        } catch (error) {
            console.error('Error creating Lambda function:', error);
            this.showToast('Error creating Lambda function', 'error');
        }
    }

    async createDataLake() {
        try {
            const bucketName = `pollution-data-lake-${Date.now()}`;
            const response = await fetch('/api/create-data-lake', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bucket_name: bucketName })
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast(`Data lake created: ${bucketName}`, 'success');
            } else {
                this.showToast('Failed to create data lake', 'error');
            }
        } catch (error) {
            console.error('Error creating data lake:', error);
            this.showToast('Error creating data lake', 'error');
        }
    }

    async uploadPollutionData() {
        try {
            const pollutionData = {
                location: 'Mediterranean Sea',
                pollution_level: 9.1,
                microplastics: 9279,
                timestamp: new Date().toISOString()
            };
            
            const response = await fetch('/api/upload-pollution-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    bucket_name: 'pollution-data-lake-demo',
                    data: pollutionData,
                    data_type: 'sensor_data'
                })
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast('Pollution data uploaded successfully', 'success');
            } else {
                this.showToast('Failed to upload pollution data', 'error');
            }
        } catch (error) {
            console.error('Error uploading pollution data:', error);
            this.showToast('Error uploading pollution data', 'error');
        }
    }

    async createBackup() {
        try {
            const response = await fetch('/api/create-backup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_bucket: 'pollution-data-lake-demo',
                    backup_bucket: `pollution-backup-${Date.now()}`
                })
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast(`Backup created: ${result.objects_backed_up} objects`, 'success');
            } else {
                this.showToast('Failed to create backup', 'error');
            }
        } catch (error) {
            console.error('Error creating backup:', error);
            this.showToast('Error creating backup', 'error');
        }
    }

    async createLexBot() {
        try {
            const botName = `PollutionReportBot-${Date.now()}`;
            const response = await fetch('/api/create-lex-bot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bot_name: botName })
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast(`Lex bot created: ${botName}`, 'success');
            } else {
                this.showToast('Failed to create Lex bot', 'error');
            }
        } catch (error) {
            console.error('Error creating Lex bot:', error);
            this.showToast('Error creating Lex bot', 'error');
        }
    }

    async openLexChat() {
        // Open chat interface modal
        const chatModal = new bootstrap.Modal(document.getElementById('lexChatModal'));
        chatModal.show();
    }

    async voiceReportLex() {
        try {
            const userInput = "I need to report pollution in the Mediterranean Sea. The pollution level is very high.";
            const response = await fetch('/api/voice-report-lex', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_input: userInput,
                    location: 'Mediterranean Sea'
                })
            });
            
            const result = await response.json();
            if (result.source) {
                this.showToast('Voice report processed via Lex', 'success');
            } else {
                this.showToast('Failed to process voice report', 'error');
            }
        } catch (error) {
            console.error('Error processing voice report via Lex:', error);
            this.showToast('Error processing voice report', 'error');
        }
    }

    async transcribeAudio() {
        // Create a simple audio file for demo
        const audioBlob = new Blob(['demo audio data'], { type: 'audio/mpeg' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'demo.mp3');
        formData.append('job_name', `transcribe-${Date.now()}`);
        formData.append('language_code', 'en-US');
        
        try {
            const response = await fetch('/api/transcribe-audio', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast('Audio transcription completed', 'success');
            } else {
                this.showToast('Failed to transcribe audio', 'error');
            }
        } catch (error) {
            console.error('Error transcribing audio:', error);
            this.showToast('Error transcribing audio', 'error');
        }
    }

    async multiLanguageTranscribe() {
        const audioBlob = new Blob(['demo audio data'], { type: 'audio/mpeg' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'demo.mp3');
        formData.append('language_codes', 'en-US,es-US,fr-CA');
        
        try {
            const response = await fetch('/api/multi-language-transcribe', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.status) {
                this.showToast('Multi-language transcription completed', 'success');
            } else {
                this.showToast('Failed to transcribe multi-language audio', 'error');
            }
        } catch (error) {
            console.error('Error transcribing multi-language audio:', error);
            this.showToast('Error transcribing multi-language audio', 'error');
        }
    }

    async identifySpeakers() {
        const audioBlob = new Blob(['demo audio data'], { type: 'audio/mpeg' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'demo.mp3');
        
        try {
            const response = await fetch('/api/identify-speakers', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.speakers) {
                this.showToast(`Identified ${result.total_speakers} speakers`, 'success');
            } else {
                this.showToast('Failed to identify speakers', 'error');
            }
        } catch (error) {
            console.error('Error identifying speakers:', error);
            this.showToast('Error identifying speakers', 'error');
        }
    }

    async refreshAWSServices() {
        this.showToast('AWS Services refreshed', 'success');
        // In a real implementation, you would refresh the status of all AWS services
    }

    // Lex Chat Interface Functions
    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        input.value = '';
        
        // Send to Lex API
        try {
            const response = await fetch('/api/lex-interaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_input: message,
                    bot_name: 'PollutionReportBot'
                })
            });
            
            const result = await response.json();
            if (result.response) {
                this.addChatMessage(result.response, 'bot');
            } else {
                this.addChatMessage('Sorry, I couldn\'t process your request. Please try again.', 'bot');
            }
        } catch (error) {
            console.error('Error sending chat message:', error);
            this.addChatMessage('Sorry, there was an error processing your message.', 'bot');
        }
    }

    addChatMessage(content, sender) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${sender === 'bot' ? '<i class="fas fa-robot text-info me-2"></i>' : ''}
                ${content}
            </div>
            <div class="message-time">${timeString}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async sendQuickMessage(message) {
        document.getElementById('chatInput').value = message;
        await this.sendChatMessage();
    }

    startVoiceInput() {
        this.showToast('Voice input feature coming soon!', 'info');
        // In a real implementation, you would integrate with Web Speech API
    }

    // Pollution Command Center Functions
    async loadCitizenReports() {
        try {
            const response = await fetch('/api/citizen-reports');
            const reports = await response.json();
            const list = document.getElementById('citizen-reports-list');
            const stats = document.getElementById('citizen-reports-stats');
            if (reports.length > 0) {
                list.innerHTML = reports.slice(0, 10).map(report => {
                    const location = report.location_name || (typeof report.location === 'string' ? report.location : 'Unknown');
                    const severity = report.severity || 'N/A';
                    const pollutionType = report.pollution_type || 'N/A';
                    const status = report.status || 'pending';
                    return `
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${location}</strong>
                                    <br><small class="text-muted">Type: ${pollutionType}</small>
                                    <br><small class="text-muted">Status: ${status}</small>
                                </div>
                                <span class="badge bg-${severity === 'high' ? 'danger' : severity === 'medium' ? 'warning' : 'success'}">
                                    Severity: ${severity}
                                </span>
                            </div>
                        </div>
                    `;
                }).join('');
                // Statistics: count, high priority, N/A for average level
                stats.innerHTML = `
                    <div class="card">
                        <div class="card-body">
                            <p><strong>Total Reports:</strong> ${reports.length}</p>
                            <p><strong>High Priority:</strong> ${reports.filter(r => r.severity === 'high').length}</p>
                            <p><strong>Types:</strong> ${[...new Set(reports.map(r => r.pollution_type || 'N/A'))].join(', ')}</p>
                        </div>
                    </div>
                `;
            } else {
                list.innerHTML = '<p>No citizen reports available.</p>';
                stats.innerHTML = '';
            }
        } catch (error) {
            document.getElementById('citizen-reports-list').innerHTML = '<p>Error loading citizen reports.</p>';
            document.getElementById('citizen-reports-stats').innerHTML = '';
            console.error('Error loading citizen reports:', error);
        }
    }

    async loadAIAlerts() {
        try {
            const response = await fetch('/api/ai-alerts');
            let alerts = await response.json();
            if (alerts && alerts.alerts) alerts = alerts.alerts; // support old format
            const modalBody = document.querySelector('#aiAlertsModal .modal-body');
            if (Array.isArray(alerts) && alerts.length > 0) {
                modalBody.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-bell text-warning me-2"></i>
                        <strong>AI-Generated Alerts</strong>
                    </div>
                    <div class="row">
                        <div class="col-md-8">
                            <h6>Active Alerts (${alerts.length}):</h6>
                            <div class="list-group">
                                ${alerts.map(alert => `
                                    <div class="list-group-item">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>${alert.location}</strong>
                                                <br><small class="text-muted">${alert.message}</small>
                                                <br><small class="text-info">Actions: ${alert.actions_required.join(', ')}</small>
                                            </div>
                                            <span class="badge bg-${alert.severity === 'high' ? 'danger' : 'warning'}">
                                                ${alert.severity.toUpperCase()}
                                            </span>
                                        </div>
                                        <div class="mt-2">${alert.recommendation_html || ''}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="col-md-4">
                            <h6>Alert Summary:</h6>
                            <div class="card">
                                <div class="card-body">
                                    <p><strong>Critical:</strong> ${alerts.filter(a => a.severity === 'high').length}</p>
                                    <p><strong>Medium:</strong> ${alerts.filter(a => a.severity === 'medium').length}</p>
                                    <p><strong>Total:</strong> ${alerts.length}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                modalBody.innerHTML = '<div class="alert alert-success">No AI alerts currently active.</div>';
            }
        } catch (error) {
            const modalBody = document.querySelector('#aiAlertsModal .modal-body');
            modalBody.innerHTML = '<div class="alert alert-danger">Error loading AI alerts. Please try again later.</div>';
            console.error('Error loading AI alerts:', error);
        }
    }

    async loadDataLakeInsights() {
        try {
            const response = await fetch('/api/data-lake-insights');
            const insights = await response.json();
            
            const modalBody = document.querySelector('#dataLakeModal .modal-body');
            // Defensive checks and fallback values
            const dataOverview = insights.data_overview || {};
            const cleanup = insights.cleanup_effectiveness || {};
            const trends = insights.pollution_trends || {};
            const stats = insights.statistics || {};
            
            modalBody.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-database text-info me-2"></i>
                    <strong>Data Lake Insights</strong>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <h6>Data Overview:</h6>
                        <div class="card">
                            <div class="card-body">
                                <p><strong>Total Files:</strong> ${dataOverview.total_files ?? stats.total_files ?? 'N/A'}</p>
                                <p><strong>Data Size:</strong> ${dataOverview.total_size_gb ?? 'N/A'} GB</p>
                                <p><strong>Locations Monitored:</strong> ${dataOverview.locations_monitored ?? stats.locations_monitored ?? 'N/A'}</p>
                                <p><strong>Date Range:</strong> ${(dataOverview.date_range?.earliest ?? 'N/A')} to ${(dataOverview.date_range?.latest ?? 'N/A')}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>Cleanup Effectiveness:</h6>
                        <div class="card">
                            <div class="card-body">
                                <p><strong>Waste Collected:</strong> ${cleanup.total_waste_collected_kg ?? 'N/A'} kg</p>
                                <p><strong>Hotspots Addressed:</strong> ${cleanup.hotspots_addressed ?? 'N/A'}</p>
                                <p><strong>Efficiency Rating:</strong> ${cleanup.efficiency_rating ?? 'N/A'}%</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <h6>Pollution Trends:</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="alert alert-danger">
                                    <strong>Increasing:</strong> ${(trends.increasing_regions ?? []).join(', ') || 'N/A'}
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="alert alert-warning">
                                    <strong>Stable:</strong> ${(trends.stable_regions ?? []).join(', ') || 'N/A'}
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="alert alert-success">
                                    <strong>Improving:</strong> ${(trends.improving_regions ?? []).join(', ') || 'N/A'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading data lake insights:', error);
            this.showToast('Error loading data lake insights', 'error');
        }
    }

    async loadPlasticLifecycle() {
        try {
            const response = await fetch('/api/plastic-lifecycle');
            const lifecycle = await response.json();
            const modalBody = document.querySelector('#lifecycleModal .modal-body');
            if (lifecycle && lifecycle.stages && lifecycle.stages.length > 0) {
                modalBody.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-recycle text-info me-2"></i>
                        <strong>Plastic Lifecycle Analysis</strong>
                    </div>
                    <div class="row">
                        <div class="col-md-8">
                            <h6>Lifecycle Stages:</h6>
                            <div class="list-group">
                                ${lifecycle.stages.map(stage => `
                                    <div class="list-group-item">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>${stage.stage}</strong>
                                                <br><small class="text-muted">${stage.description}</small>
                                                <br><small class="text-info">Solutions: ${stage.solutions.join(', ')}</small>
                                            </div>
                                            <span class="badge bg-${stage.impact_score > 8 ? 'danger' : stage.impact_score > 6 ? 'warning' : 'success'}">
                                                Impact: ${stage.impact_score}/10
                                            </span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="col-md-4">
                            <h6>Global Statistics:</h6>
                            <div class="card">
                                <div class="card-body">
                                    <p><strong>Annual Production:</strong> ${lifecycle.statistics.annual_production_million_tons}M tons</p>
                                    <p><strong>Ocean Plastic:</strong> ${lifecycle.statistics.ocean_plastic_million_tons}M tons</p>
                                    <p><strong>Recycling Rate:</strong> ${lifecycle.statistics.recycling_rate_percent}%</p>
                                    <p><strong>Biodegradation Time:</strong> ${lifecycle.statistics.biodegradation_time_years} years</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                modalBody.innerHTML = '<div class="alert alert-success">No lifecycle data available.</div>';
            }
        } catch (error) {
            const modalBody = document.querySelector('#lifecycleModal .modal-body');
            modalBody.innerHTML = '<div class="alert alert-danger">Error loading plastic lifecycle data. Please try again later.</div>';
            console.error('Error loading plastic lifecycle:', error);
        }
    }

    async loadGlobalImpact() {
        try {
            const response = await fetch('/api/global-impact');
            const impact = await response.json();
            
            const modalBody = document.querySelector('#impactModal .modal-body');
            modalBody.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-globe text-warning me-2"></i>
                    <strong>Global Impact Assessment</strong>
                </div>
                <div class="row">
                    <div class="col-md-6">
                        <h6>Current Status:</h6>
                        <div class="card">
                            <div class="card-body">
                                <p><strong>Oceans Affected:</strong> ${impact.current_status.total_oceans_affected}</p>
                                <p><strong>Marine Species at Risk:</strong> ${impact.current_status.marine_species_at_risk}</p>
                                <p><strong>Coastal Communities:</strong> ${impact.current_status.coastal_communities_impacted}</p>
                                <p><strong>Economic Cost:</strong> $${impact.current_status.economic_cost_billion_usd}B</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>Regional Analysis:</h6>
                        <div class="list-group">
                            ${impact.regional_analysis.map(region => `
                                <div class="list-group-item">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <div>
                                            <strong>${region.region}</strong>
                                            <br><small class="text-muted">Level: ${region.pollution_level} | Trend: ${region.trend}</small>
                                        </div>
                                        <span class="badge bg-${region.impact === 'severe' ? 'danger' : region.impact === 'high' ? 'warning' : 'success'}">
                                            ${region.impact}
                                        </span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <h6>AI Recommendations:</h6>
                        <ul class="list-group">
                            ${impact.ai_recommendations.map(rec => `
                                <li class="list-group-item">
                                    <i class="fas fa-lightbulb text-warning me-2"></i>
                                    ${rec}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading global impact:', error);
            this.showToast('Error loading global impact data', 'error');
        }
    }

    async loadEngageActions() {
        try {
            const response = await fetch('/api/engage-actions');
            const engage = await response.json();
            const modalBody = document.querySelector('#engageModal .modal-body');
            if (engage && engage.citizen_actions && engage.citizen_actions.length > 0) {
                modalBody.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-hands-helping text-success me-2"></i>
                        <strong>Engagement Opportunities</strong>
                    </div>
                    <div class="row">
                        <div class="col-md-4">
                            <h6>Citizen Actions:</h6>
                            <div class="list-group">
                                ${engage.citizen_actions.map(action => `
                                    <div class="list-group-item">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>${action.action}</strong>
                                                <br><small class="text-muted">${action.description}</small>
                                            </div>
                                            <span class="badge bg-${action.impact === 'high' ? 'success' : 'primary'}">
                                                ${action.impact}
                                            </span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="col-md-4">
                            <h6>Organization Actions:</h6>
                            <div class="list-group">
                                ${engage.organization_actions.map(action => `
                                    <div class="list-group-item">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>${action.action}</strong>
                                                <br><small class="text-muted">${action.description}</small>
                                            </div>
                                            <span class="badge bg-${action.impact === 'very_high' ? 'danger' : 'warning'}">
                                                ${action.impact}
                                            </span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="col-md-4">
                            <h6>Government Actions:</h6>
                            <div class="list-group">
                                ${engage.government_actions.map(action => `
                                    <div class="list-group-item">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <div>
                                                <strong>${action.action}</strong>
                                                <br><small class="text-muted">${action.description}</small>
                                            </div>
                                            <span class="badge bg-${action.impact === 'very_high' ? 'danger' : 'warning'}">
                                                ${action.impact}
                                            </span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6>Success Stories:</h6>
                            <div class="row">
                                ${engage.success_stories.map(story => `
                                    <div class="col-md-6">
                                        <div class="card">
                                            <div class="card-body">
                                                <h6 class="card-title">${story.title}</h6>
                                                <p class="card-text">${story.description}</p>
                                                <p class="card-text"><small class="text-muted">Impact: ${story.impact}</small></p>
                                                <p class="card-text"><small class="text-muted">Participants: ${story.participants}</small></p>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `;
            } else {
                modalBody.innerHTML = '<div class="alert alert-success">No engagement data available.</div>';
            }
        } catch (error) {
            const modalBody = document.querySelector('#engageModal .modal-body');
            modalBody.innerHTML = '<div class="alert alert-danger">Error loading engagement data. Please try again later.</div>';
            console.error('Error loading engage actions:', error);
        }
    }

    async loadHotspotModal() {
        try {
            const response = await fetch('/api/sensor-data');
            const sensors = await response.json();
            const hotspots = sensors.filter(s => s.pollution_level >= 7);
            const modalBody = document.querySelector('#hotspotModal .modal-body');
            if (hotspots.length > 0) {
                modalBody.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-fire text-danger me-2"></i>
                        <strong>Detected Hotspots (${hotspots.length})</strong>
                    </div>
                    <div class="list-group">
                        ${hotspots.map(h => `
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>${h.location}</strong>
                                        <br><small class="text-muted">Algae Bloom Level: ${h.pollution_level}/10</small>
                                        <br><small>Microalgae: ${h.microplastics.toLocaleString()} cells/L</small>
                                    </div>
                                    <span class="badge bg-${h.pollution_level >= 9 ? 'danger' : 'warning'}">${h.status.toUpperCase()}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                modalBody.innerHTML = '<p>No pollution hotspots detected at this time.</p>';
            }
        } catch (error) {
            const modalBody = document.querySelector('#hotspotModal .modal-body');
            modalBody.innerHTML = '<p>Error loading hotspot data.</p>';
            console.error('Error loading hotspot modal:', error);
        }
    }

    async loadMicroplasticsModal() {
        try {
            const response = await fetch('/api/sensor-data');
            const sensors = await response.json();
            const modalBody = document.querySelector('#microplasticsModal .modal-body');
            if (sensors.length > 0) {
                const sorted = sensors.slice().sort((a, b) => b.microplastics - a.microplastics);
                modalBody.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-tint text-info me-2"></i>
                        <strong>Microplastics Concentration by Location</strong>
                    </div>
                    <div class="list-group">
                        ${sorted.map(s => `
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>${s.location}</strong>
                                        <br><small class="text-muted">${s.lat.toFixed(2)}, ${s.lng.toFixed(2)}</small>
                                    </div>
                                    <span class="badge bg-${s.microplastics > 7000 ? 'danger' : s.microplastics > 4000 ? 'warning' : 'success'}">
                                        ${s.microplastics.toLocaleString()} cells/L
                                    </span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                modalBody.innerHTML = '<p>No microplastics data available.</p>';
            }
        } catch (error) {
            const modalBody = document.querySelector('#microplasticsModal .modal-body');
            modalBody.innerHTML = '<p>Error loading microplastics data.</p>';
            console.error('Error loading microplastics modal:', error);
        }
    }

    async loadCleanupModal() {
        try {
            const response = await fetch('/api/cleanup-missions');
            const data = await response.json();
            const missions = data.missions || [];
            const modalBody = document.querySelector('#cleanupModal .modal-body');
            if (missions.length > 0) {
                modalBody.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-robot text-success me-2"></i>
                        <strong>Active Cleanup Missions (${missions.length})</strong>
                    </div>
                    <div class="list-group mb-3">
                        ${missions.map(m => `
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>${m.location || m.mission_id}</strong>
                                        <br><small class="text-muted">Status: ${m.status}</small>
                                        <br><small>Robots: ${m.robots ? Object.entries(m.robots).map(([k,v]) => `${k}: ${v}`).join(', ') : 'N/A'}</small>
                                    </div>
                                    <span class="badge bg-${m.status === 'active' ? 'success' : 'secondary'}">${m.status.toUpperCase()}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                    <div class="card">
                        <div class="card-body">
                            <p><strong>Total Resources:</strong> Ocean Drones: ${data.total_resources.ocean_drones}, Surface Vessels: ${data.total_resources.surface_vessels}, Underwater Units: ${data.total_resources.underwater_units}</p>
                            <p><strong>Waste Collected Today:</strong> ${data.daily_stats.waste_collected_today} kg</p>
                            <p><strong>Hotspots Addressed:</strong> ${data.daily_stats.hotspots_addressed}</p>
                        </div>
                    </div>
                `;
            } else {
                modalBody.innerHTML = '<p>No active cleanup missions at this time.</p>';
            }
        } catch (error) {
            const modalBody = document.querySelector('#cleanupModal .modal-body');
            modalBody.innerHTML = '<p>Error loading cleanup missions.</p>';
            console.error('Error loading cleanup modal:', error);
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aquaPulseDashboard = new AquaPulseDashboard();
    // Multi-Agent AI Optimization System: Optimize button logic
    setTimeout(() => {
        const optimizeBtn = document.getElementById('optimize-btn');
        const spinner = document.getElementById('optimize-btn-spinner');
        if (optimizeBtn && spinner) {
            optimizeBtn.addEventListener('click', async () => {
                optimizeBtn.disabled = true;
                spinner.style.display = 'inline-block';
                // Optionally, hide metrics/log during optimization
                const metricsRow = document.querySelector('#aiAgentModal .row.mb-4');
                const metricsTable = document.querySelector('#aiAgentModal .row.mt-4');
                const log = document.getElementById('optimization-log');
                if (metricsRow) metricsRow.style.opacity = 0.3;
                if (metricsTable) metricsTable.style.opacity = 0.3;
                if (log) log.style.opacity = 0.3;
                // Simulate AWS Bedrock optimization (3-4 seconds)
                await new Promise(res => setTimeout(res, 3200 + Math.random() * 800));
                // Show results
                if (metricsRow) metricsRow.style.opacity = 1;
                if (metricsTable) metricsTable.style.opacity = 1;
                if (log) log.style.opacity = 1;
                spinner.style.display = 'none';
                optimizeBtn.disabled = false;
            });
        }
    }, 500);
});

// Global AWS Service Functions for HTML onclick handlers
window.createIoTThing = () => window.aquaPulseDashboard.createIoTThing();
window.publishIoTMessage = () => window.aquaPulseDashboard.publishIoTMessage();
window.showIoTStatus = () => window.aquaPulseDashboard.showIoTStatus();
window.createLambdaFunction = (type) => window.aquaPulseDashboard.createLambdaFunction(type);
window.createDataLake = () => window.aquaPulseDashboard.createDataLake();
window.uploadPollutionData = () => window.aquaPulseDashboard.uploadPollutionData();
window.createBackup = () => window.aquaPulseDashboard.createBackup();
window.createLexBot = () => window.aquaPulseDashboard.createLexBot();
window.openLexChat = () => window.aquaPulseDashboard.openLexChat();
window.voiceReportLex = () => window.aquaPulseDashboard.voiceReportLex();
window.transcribeAudio = () => window.aquaPulseDashboard.transcribeAudio();
window.multiLanguageTranscribe = () => window.aquaPulseDashboard.multiLanguageTranscribe();
window.identifySpeakers = () => window.aquaPulseDashboard.identifySpeakers();
window.refreshAWSServices = () => window.aquaPulseDashboard.refreshAWSServices();

// Global Chat Functions
window.sendChatMessage = () => window.aquaPulseDashboard.sendChatMessage();
window.sendQuickMessage = (message) => window.aquaPulseDashboard.sendQuickMessage(message);
window.startVoiceInput = () => window.aquaPulseDashboard.startVoiceInput();
window.handleChatKeyPress = (event) => {
    if (event.key === 'Enter') {
        window.sendChatMessage();
    }
};

// Modal openers
window.showHotspotModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('hotspotModal'));
    modal.show();
    window.aquaPulseDashboard.loadHotspotModal();
};
window.showMicroplasticsModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('microplasticsModal'));
    modal.show();
    window.aquaPulseDashboard.loadMicroplasticsModal();
};
window.showCleanupModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('cleanupModal'));
    modal.show();
    window.aquaPulseDashboard.loadCleanupModal();
};
window.showCitizenModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('citizenModal'));
    modal.show();
    window.aquaPulseDashboard.loadCitizenReports();
};
window.showAIAlertsModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('aiAlertsModal'));
    modal.show();
    window.aquaPulseDashboard.loadAIAlerts();
};
window.showDataLakeModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('dataLakeModal'));
    modal.show();
    window.aquaPulseDashboard.loadDataLakeInsights();
};
window.showLifecycleModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('lifecycleModal'));
    modal.show();
    window.aquaPulseDashboard.loadPlasticLifecycle();
};
window.showImpactModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('impactModal'));
    modal.show();
    window.aquaPulseDashboard.loadGlobalImpact();
};
window.showEngageModal = () => {
    const modal = new bootstrap.Modal(document.getElementById('engageModal'));
    modal.show();
    window.aquaPulseDashboard.loadEngageActions();
};
window.showDeleteJunkModal = () => new bootstrap.Modal(document.getElementById('deleteJunkModal')).show();

// Delete junk services
window.deleteJunkServices = async () => {
    const btn = document.querySelector('#deleteJunkModal .btn-danger');
    btn.disabled = true;
    btn.textContent = 'Deleting...';
    try {
        const response = await fetch('/api/delete-junk-services', { method: 'POST' });
        const result = await response.json();
        if (result.status === 'deleted') {
            btn.textContent = 'Deleted!';
            setTimeout(() => location.reload(), 1200);
        } else {
            btn.textContent = 'Error';
        }
    } catch (e) {
        btn.textContent = 'Error';
    }
    setTimeout(() => {
        btn.disabled = false;
        btn.textContent = 'Delete';
    }, 2000);
};

// Recreate demo services
window.recreateDemoServices = async () => {
    const btn = document.querySelector('.btn-success[onclick="recreateDemoServices()"]');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recreating...';
    
    try {
        // Create essential services
        await window.aquaPulseDashboard.createIoTThing();
        await window.aquaPulseDashboard.createLambdaFunction('data_processor');
        await window.aquaPulseDashboard.createDataLake();
        await window.aquaPulseDashboard.createLexBot();
        
        btn.innerHTML = '<i class="fas fa-check"></i> Recreated!';
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            location.reload();
        }, 1500);
    } catch (error) {
        console.error('Error recreating services:', error);
        btn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }, 2000);
    }
};

// Map Animations: 50+ overlays/markers
window.animateMap = () => {
    if (!window.pollutionMap) return;
    // Remove old overlays
    if (window._animatedMarkers) {
        window._animatedMarkers.forEach(m => window.pollutionMap.removeLayer(m));
    }
    window._animatedMarkers = [];
    // Add 50+ animated overlays
    for (let i = 0; i < 50; i++) {
        const lat = 30 + Math.random() * 40;
        const lng = -80 + Math.random() * 160;
        const iconType = i % 5;
        let iconHtml = '';
        if (iconType === 0) iconHtml = '<i class="fas fa-recycle text-success"></i>';
        if (iconType === 1) iconHtml = '<i class="fas fa-bottle-water text-primary"></i>';
        if (iconType === 2) iconHtml = '<i class="fas fa-robot text-warning"></i>';
        if (iconType === 3) iconHtml = '<i class="fas fa-exclamation-triangle text-danger"></i>';
        if (iconType === 4) iconHtml = '<i class="fas fa-water text-info"></i>';
        const marker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'animated-map-icon',
                html: iconHtml,
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            })
        }).addTo(window.pollutionMap);
        window._animatedMarkers.push(marker);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => window.animateMap && window.animateMap(), 1000);
});

// Hotspot Detection Modal Logic
window.aquaPulseDashboard.loadHotspotModal = async function() {
    // Fetch IoT sensor data, Lambda status, Bedrock AI analysis, and S3 download link
    try {
        const [sensorsRes, lambdaRes, aiRes, s3Res] = await Promise.all([
            fetch('/api/sensor-data'),
            fetch('/api/aws-services-status'),
            fetch('/api/ai-analysis'),
            fetch('/api/download-hotspot-data')
        ]);
        const sensors = await sensorsRes.json();
        const lambdaStatus = await lambdaRes.json();
        const aiAnalysis = await aiRes.json();
        const s3Link = await s3Res.json();
        // Populate map (assume map logic exists)
        if (window.pollutionMap && sensors.length) {
            window.pollutionMap.setView([sensors[0].lat, sensors[0].lng], 4);
            window.pollutionMap.clearLayers();
            sensors.forEach(s => {
                L.marker([s.lat, s.lng]).addTo(window.pollutionMap).bindPopup(`<b>${s.location}</b><br>Level: ${s.pollution_level}`);
            });
        }
        document.getElementById('lambda-status').innerHTML = `<span class='badge bg-${lambdaStatus.lambda_functions ? 'success' : 'secondary'}'>${lambdaStatus.lambda_functions || 'Unavailable'}</span>`;
        document.getElementById('ai-hotspots').innerHTML = aiAnalysis.html || aiAnalysis.analysis;
        document.getElementById('download-hotspot-data').href = s3Link.url || '#';
    } catch (e) {
        document.getElementById('lambda-status').textContent = 'Error loading Lambda status.';
        document.getElementById('ai-hotspots').textContent = 'Error loading AI analysis.';
    }
};

// Microplastics Analytics Modal Logic
window.aquaPulseDashboard.loadMicroplasticsModal = async function() {
    try {
        const [mlRes, s3Res] = await Promise.all([
            fetch('/api/microplastics-analytics'),
            fetch('/api/download-microplastics-report')
        ]);
        const mlData = await mlRes.json();
        const s3Link = await s3Res.json();
        // Populate chart (assume Chart.js)
        if (window.microplasticsChart && mlData.chart) {
            window.microplasticsChart.data = mlData.chart;
            window.microplasticsChart.update();
        }
        document.getElementById('microplastics-data-explorer').innerHTML = mlData.data_explorer || 'No data.';
        document.getElementById('download-microplastics-report').href = s3Link.url || '#';
    } catch (e) {
        document.getElementById('microplastics-data-explorer').textContent = 'Error loading data.';
    }
};

document.getElementById('run-deep-analysis').onclick = async function() {
    this.disabled = true;
    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
    try {
        await fetch('/api/run-deep-microplastics-analysis', { method: 'POST' });
        window.aquaPulseDashboard.loadMicroplasticsModal();
    } finally {
        this.disabled = false;
        this.innerHTML = '<i class="fas fa-bolt me-1"></i>Run Deep Analysis (Lambda/SageMaker)';
    }
};

// Cleanup Missions Modal Logic
window.aquaPulseDashboard.loadCleanupModal = async function() {
    try {
        const [missionsRes, s3Res] = await Promise.all([
            fetch('/api/cleanup-missions'),
            fetch('/api/download-mission-logs')
        ]);
        const missions = await missionsRes.json();
        const s3Link = await s3Res.json();
        document.getElementById('cleanup-mission-dashboard').innerHTML = missions.dashboard_html || 'No data.';
        document.getElementById('robot-status').innerHTML = missions.robot_status || 'No status.';
        document.getElementById('download-mission-logs').href = s3Link.url || '#';
    } catch (e) {
        document.getElementById('cleanup-mission-dashboard').textContent = 'Error loading missions.';
    }
};

window.launchAIOptimization = async function() {
    // Show overlay
    const overlay = document.getElementById('aiOptimizationOverlay');
    const text = document.getElementById('ai-optimization-text');
    if (!overlay || !text) return;
    const modal = new bootstrap.Modal(overlay, {backdrop: 'static', keyboard: false});
    modal.show();
    // Animation sequence
    const steps = [
        'Optimizing using AWS Bedrock...',
        'Solving with multiple agents...',
        'Coordinating AI resources...',
        'Finalizing optimization...'
    ];
    let idx = 0;
    const interval = setInterval(() => {
        idx++;
        if (idx < steps.length) {
            text.textContent = steps[idx];
        }
    }, 900);
    // Wait 3.2-4s, then hide overlay and show AI Agent modal
    await new Promise(res => setTimeout(res, 3200 + Math.random() * 800));
    clearInterval(interval);
    modal.hide();
    setTimeout(() => {
        const aiModal = new bootstrap.Modal(document.getElementById('aiAgentModal'));
        aiModal.show();
    }, 400);
};

// --- Citizen Reports & Engagement Demo Logic ---

// Voice Report Demo
window.startDemoVoiceRecording = function() {
    // Simulate recording UI
    const recordBtn = document.getElementById('voice-record-btn');
    const analysisDiv = document.getElementById('voice-report-analysis');
    if (recordBtn) {
        recordBtn.disabled = true;
        recordBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recording...';
        setTimeout(() => {
            recordBtn.innerHTML = '<i class="fas fa-microphone"></i> Click to start recording';
            recordBtn.disabled = false;
            if (analysisDiv) {
                analysisDiv.innerHTML = `
                    <div class="alert alert-info mt-2">
                        <strong>Voice Report Transcript:</strong><br>
                        "There is a visible green algae bloom near the shore in the Mediterranean Sea. Water is discolored and there is a strong odor."
                        <hr>
                        <strong>AI Analysis:</strong><br>
                        <ul>
                            <li>Location: Mediterranean Sea</li>
                            <li>Severity: High</li>
                            <li>Recommended Action: Immediate investigation and mitigation</li>
                        </ul>
                    </div>
                `;
            }
        }, 2000);
    }
};

// Chat Demo
window.sendDemoChatMessage = function() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    window.aquaPulseDashboard.addChatMessage(message, 'user');
    input.value = '';
    setTimeout(() => {
        window.aquaPulseDashboard.addChatMessage(
            'Thank you for your report. Our team will review the algae bloom incident and update you soon. 🌊',
            'bot'
        );
    }, 1200);
};
