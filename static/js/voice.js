// AquaPulse - Voice Interaction JavaScript

class VoiceController {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.synthesis = window.speechSynthesis;
        this.init();
    }

    init() {
        this.setupSpeechRecognition();
        this.setupEventListeners();
    }

    setupSpeechRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
        } else if ('SpeechRecognition' in window) {
            this.recognition = new SpeechRecognition();
        }

        if (this.recognition) {
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                this.onListeningStart();
            };

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.processVoiceCommand(transcript);
            };

            this.recognition.onerror = (event) => {
                this.onListeningError(event.error);
            };

            this.recognition.onend = () => {
                this.onListeningEnd();
            };
        }
    }

    setupEventListeners() {
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => {
                this.toggleListening();
            });
        }
    }

    toggleListening() {
        if (!this.recognition) {
            this.showVoiceError('Speech recognition not supported in this browser');
            return;
        }

        if (this.isListening) {
            this.stopListening();
        } else {
            this.startListening();
        }
    }

    startListening() {
        try {
            this.recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.showVoiceError('Could not start voice recognition');
        }
    }

    stopListening() {
        if (this.recognition) {
            this.recognition.stop();
        }
    }

    onListeningStart() {
        this.isListening = true;
        this.updateVoiceStatus('Listening... Speak now');
        this.updateVoiceButton(true);
    }

    onListeningEnd() {
        this.isListening = false;
        this.updateVoiceStatus('Click to start voice interaction');
        this.updateVoiceButton(false);
    }

    onListeningError(error) {
        this.isListening = false;
        console.error('Speech recognition error:', error);
        this.updateVoiceStatus('Voice recognition error');
        this.updateVoiceButton(false);
    }

    updateVoiceStatus(message) {
        const statusElement = document.getElementById('voice-status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    updateVoiceButton(listening) {
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            const icon = voiceBtn.querySelector('i');
            if (listening) {
                voiceBtn.classList.add('btn-danger');
                voiceBtn.classList.remove('btn-primary');
                icon.className = 'fas fa-stop';
            } else {
                voiceBtn.classList.add('btn-primary');
                voiceBtn.classList.remove('btn-danger');
                icon.className = 'fas fa-microphone';
            }
        }
    }

    async processVoiceCommand(transcript) {
        console.log('Voice command received:', transcript);
        this.updateVoiceStatus(`Processing: "${transcript}"`);

        const command = transcript.toLowerCase();

        try {
            if (command.includes('refresh') || command.includes('update')) {
                this.speak('Refreshing dashboard data');
                await window.gppnnDashboard.refreshAllData();
                
            } else if (command.includes('report') || command.includes('pollution')) {
                this.speak('Opening pollution report form');
                const reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
                reportModal.show();
                
            } else if (command.includes('status') || command.includes('summary')) {
                this.provideDashboardSummary();
                
            } else if (command.includes('analysis') || command.includes('ai')) {
                this.speak('Playing AI analysis');
                await window.playAnalysis();
                
            } else if (command.includes('help')) {
                this.provideVoiceHelp();
                
            } else {
                // Send to AI for interpretation
                await this.sendToAI(transcript);
            }
        } catch (error) {
            console.error('Error processing voice command:', error);
            this.speak('Sorry, I encountered an error processing your request');
        }

        this.updateVoiceStatus('Click to start voice interaction');
    }

    async sendToAI(query) {
        try {
            // This would integrate with Amazon Lex in a full implementation
            // For now, provide a general response
            this.speak(`I heard you say: ${query}. Let me check the current pollution data for you.`);
            
            // Get current sensor data
            const response = await fetch('/api/sensor-data');
            const sensors = await response.json();
            
            const highPollutionAreas = sensors.filter(s => s.pollution_level >= 7);
            
            if (highPollutionAreas.length > 0) {
                const areas = highPollutionAreas.map(s => s.location).join(', ');
                this.speak(`I found high pollution levels in the following areas: ${areas}`);
            } else {
                this.speak('All monitored areas are currently showing normal pollution levels');
            }
        } catch (error) {
            console.error('Error sending to AI:', error);
            this.speak('Sorry, I could not process your request at the moment');
        }
    }

    provideDashboardSummary() {
        try {
            const sensorData = JSON.parse(document.getElementById('sensor-data').textContent);
            const activeSensors = sensorData.length;
            const warningAreas = sensorData.filter(s => s.status === 'warning').length;
            
            let summary = `Dashboard summary: ${activeSensors} sensors are currently active. `;
            
            if (warningAreas > 0) {
                summary += `${warningAreas} areas are showing high pollution levels and require attention. `;
            } else {
                summary += 'All areas are showing normal pollution levels. ';
            }
            
            summary += 'The neural network is operating normally and cleanup operations are ongoing.';
            
            this.speak(summary);
        } catch (error) {
            console.error('Error providing summary:', error);
            this.speak('Sorry, I could not generate a summary at this time');
        }
    }

    provideVoiceHelp() {
        const helpText = `
            Voice commands you can use:
            Say "refresh" or "update" to refresh the dashboard.
            Say "report pollution" to open the reporting form.
            Say "status" or "summary" for a dashboard overview.
            Say "analysis" to hear the AI analysis.
            You can also ask questions about pollution levels or specific areas.
        `;
        this.speak(helpText);
    }

    speak(text) {
        if (this.synthesis) {
            // Cancel any ongoing speech
            this.synthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 0.8;
            
            // Try to use a specific voice if available
            const voices = this.synthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.name.includes('Google') || 
                voice.name.includes('Microsoft') ||
                voice.lang.startsWith('en')
            );
            
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }
            
            this.synthesis.speak(utterance);
        } else {
            // Fallback: use Polly API
            this.speakWithPolly(text);
        }
    }

    async speakWithPolly(text) {
        try {
            const response = await fetch('/api/synthesize-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    voice_id: 'Joanna'
                })
            });

            const data = await response.json();
            
            if (data.audio) {
                // Convert base64 to audio and play
                const audioData = atob(data.audio);
                const audioArray = new Uint8Array(audioData.length);
                for (let i = 0; i < audioData.length; i++) {
                    audioArray[i] = audioData.charCodeAt(i);
                }
                
                const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                
                audio.play().catch(error => {
                    console.error('Error playing Polly audio:', error);
                });
            }
        } catch (error) {
            console.error('Error with Polly speech synthesis:', error);
        }
    }

    showVoiceError(message) {
        this.updateVoiceStatus(message);
        setTimeout(() => {
            this.updateVoiceStatus('Click to start voice interaction');
        }, 3000);
    }
}

// Initialize voice controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.voiceController = new VoiceController();
});
