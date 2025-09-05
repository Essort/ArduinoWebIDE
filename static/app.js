/**
 * Arduino Web IDE - Main Application
 * Handles CodeMirror editor, Arduino CLI integration, serial monitoring, and AI assistance
 */

class ArduinoIDE {
    constructor() {
        this.editor = null;
        this.currentSketch = 'Untitled.ino';
        this.serialSocket = null;
        this.isSerialConnected = false;
        this.currentPort = null;
        
        this.init();
    }
    
    async init() {
        this.setupEditor();
        this.setupEventListeners();
        await this.loadBoards();
        await this.loadPorts();
        await this.loadSketches();
        await this.loadTemplates();
        await this.checkOllamaStatus();
        
        console.log('Arduino IDE initialized');
    }
    
    setupEditor() {
        // Arduino-specific keywords and functions
        const arduinoKeywords = {
            // Core functions
            'setup': true, 'loop': true,
            // Digital I/O
            'pinMode': true, 'digitalWrite': true, 'digitalRead': true,
            // Analog I/O
            'analogRead': true, 'analogWrite': true, 'analogReference': true,
            // Time
            'delay': true, 'delayMicroseconds': true, 'millis': true, 'micros': true,
            // Serial
            'Serial': true, 'print': true, 'println': true, 'begin': true, 'available': true, 'read': true,
            // Math
            'min': true, 'max': true, 'abs': true, 'constrain': true, 'map': true, 'pow': true, 'sqrt': true,
            // Trigonometry
            'sin': true, 'cos': true, 'tan': true,
            // Random
            'random': true, 'randomSeed': true,
            // Bits and Bytes
            'lowByte': true, 'highByte': true, 'bitRead': true, 'bitWrite': true, 'bitSet': true, 'bitClear': true,
            // External Interrupts
            'attachInterrupt': true, 'detachInterrupt': true,
            // Tone
            'tone': true, 'noTone': true,
            // Libraries
            'Servo': true, 'SoftwareSerial': true, 'Wire': true, 'SPI': true, 'EEPROM': true,
            // Constants
            'HIGH': true, 'LOW': true, 'INPUT': true, 'OUTPUT': true, 'INPUT_PULLUP': true,
            'LED_BUILTIN': true, 'A0': true, 'A1': true, 'A2': true, 'A3': true, 'A4': true, 'A5': true
        };
        
        // Custom hint function for Arduino
        CodeMirror.registerHelper('hint', 'arduino', function(editor) {
            const cur = editor.getCursor();
            const token = editor.getTokenAt(cur);
            const start = token.start;
            const end = cur.ch;
            const word = token.string.slice(0, end - start);
            
            const suggestions = Object.keys(arduinoKeywords)
                .filter(key => key.toLowerCase().includes(word.toLowerCase()))
                .map(key => ({ text: key, displayText: key }));
            
            return {
                list: suggestions,
                from: CodeMirror.Pos(cur.line, start),
                to: CodeMirror.Pos(cur.line, end)
            };
        });
        
        // Initialize CodeMirror editor
        const textarea = document.getElementById('codeEditor');
        this.editor = CodeMirror.fromTextArea(textarea, {
            mode: 'text/x-c++src',
            theme: 'monokai',
            lineNumbers: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 2,
            tabSize: 2,
            indentWithTabs: false,
            extraKeys: {
                'Ctrl-Space': 'autocomplete',
                'Ctrl-S': () => this.saveCurrentSketch(),
                'Ctrl-R': () => this.compileSketch(),
                'Ctrl-U': () => this.uploadSketch(),
                'F9': () => this.compileSketch(),
                'F10': () => this.uploadSketch()
            },
            hintOptions: {
                hint: CodeMirror.hint.arduino,
                completeSingle: false
            }
        });
        
        // Auto-save on change
        this.editor.on('change', () => {
            this.markUnsaved();
        });
        
        // Auto-complete on typing
        this.editor.on('inputRead', (cm, event) => {
            if (event.text[0].match(/[a-zA-Z]/)) {
                CodeMirror.commands.autocomplete(cm, null, {completeSingle: false});
            }
        });
    }
    
    setupEventListeners() {
        // Toolbar buttons
        document.getElementById('verifyBtn').addEventListener('click', () => this.compileSketch());
        document.getElementById('uploadBtn').addEventListener('click', () => this.uploadSketch());
        document.getElementById('serialMonitorBtn').addEventListener('click', () => this.toggleSerialMonitor());
        
        // File operations
        document.getElementById('newSketchBtn').addEventListener('click', () => this.showNewSketchModal());
        document.getElementById('saveSketchBtn').addEventListener('click', () => this.saveCurrentSketch());
        document.getElementById('refreshPorts').addEventListener('click', () => this.loadPorts());
        
        // Output tabs
        document.querySelectorAll('.output-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchOutputTab(e.target.dataset.tab);
            });
        });
        
        // AI tabs
        document.querySelectorAll('.ai-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchAITab(e.target.dataset.tab);
            });
        });
        
        // AI buttons
        document.getElementById('generateCode').addEventListener('click', () => this.generateCode());
        document.getElementById('reviewCode').addEventListener('click', () => this.reviewCode());
        
        // Serial monitor
        document.getElementById('connectSerial').addEventListener('click', () => this.toggleSerialConnection());
        document.getElementById('sendSerial').addEventListener('click', () => this.sendSerialData());
        document.getElementById('serialInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendSerialData();
        });
        document.getElementById('clearSerial').addEventListener('click', () => this.clearSerial());
        document.getElementById('clearConsole').addEventListener('click', () => this.clearConsole());
        
        // Modal handlers
        document.getElementById('createSketch').addEventListener('click', () => this.createNewSketch());
        document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
            btn.addEventListener('click', () => this.hideModals());
        });
        
        // Board and port selectors
        document.getElementById('boardSelect').addEventListener('change', (e) => {
            console.log('Board selected:', e.target.value);
        });
        
        document.getElementById('portSelect').addEventListener('change', (e) => {
            this.currentPort = e.target.value;
            console.log('Port selected:', e.target.value);
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 's') {
                    e.preventDefault();
                    this.saveCurrentSketch();
                } else if (e.key === 'r') {
                    e.preventDefault();
                    this.compileSketch();
                } else if (e.key === 'u') {
                    e.preventDefault();
                    this.uploadSketch();
                }
            }
        });
    }
    
    async loadBoards() {
        try {
            const response = await fetch('/api/boards');
            const data = await response.json();
            const select = document.getElementById('boardSelect');
            
            select.innerHTML = '<option value="">Select Board...</option>';
            
            Object.entries(data.boards).forEach(([fqbn, name]) => {
                const option = document.createElement('option');
                option.value = fqbn;
                option.textContent = name;
                select.appendChild(option);
            });
            
            // Select Arduino Uno as default
            select.value = 'arduino:avr:uno';
        } catch (error) {
            console.error('Failed to load boards:', error);
            this.addConsoleMessage('Failed to load boards', 'error');
        }
    }
    
    async loadPorts() {
        try {
            const response = await fetch('/api/ports');
            const data = await response.json();
            const select = document.getElementById('portSelect');
            
            select.innerHTML = '<option value="">Select Port...</option>';
            
            data.ports.forEach(port => {
                const option = document.createElement('option');
                option.value = port.device;
                option.textContent = `${port.device} (${port.description})`;
                select.appendChild(option);
            });
            
            // Auto-select first available port
            if (data.ports.length > 0) {
                select.value = data.ports[0].device;
                this.currentPort = data.ports[0].device;
            }
        } catch (error) {
            console.error('Failed to load ports:', error);
            this.addConsoleMessage('Failed to load ports', 'error');
        }
    }
    
    async loadSketches() {
        try {
            const response = await fetch('/api/sketches');
            const data = await response.json();
            const list = document.getElementById('sketchesList');
            
            list.innerHTML = '';
            
            data.sketches.forEach(sketch => {
                const li = document.createElement('li');
                li.innerHTML = `<i class="fas fa-file-code"></i> ${sketch.name}`;
                li.addEventListener('click', () => this.loadSketch(sketch.name));
                
                // Add context menu for delete
                li.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    if (confirm(`Delete sketch "${sketch.name}"?`)) {
                        this.deleteSketch(sketch.name);
                    }
                });
                
                list.appendChild(li);
            });
        } catch (error) {
            console.error('Failed to load sketches:', error);
        }
    }
    
    async loadTemplates() {
        try {
            const response = await fetch('/api/templates');
            const data = await response.json();
            const list = document.getElementById('templatesList');
            
            list.innerHTML = '';
            
            data.templates.forEach(template => {
                const li = document.createElement('li');
                li.innerHTML = `<i class="fas fa-file-alt"></i> ${template.name}`;
                li.addEventListener('click', () => this.loadTemplate(template.name));
                list.appendChild(li);
            });
        } catch (error) {
            console.error('Failed to load templates:', error);
        }
    }
    
    async loadSketch(sketchName) {
        try {
            const response = await fetch(`/api/sketch/${sketchName}`);
            const data = await response.json();
            
            this.editor.setValue(data.content);
            this.currentSketch = sketchName;
            this.updateTabName(sketchName);
            this.addConsoleMessage(`Loaded sketch: ${sketchName}`, 'info');
            
            // Highlight current sketch in file list
            document.querySelectorAll('.file-list li').forEach(li => li.classList.remove('active'));
            event.target.classList.add('active');
        } catch (error) {
            console.error('Failed to load sketch:', error);
            this.addConsoleMessage(`Failed to load sketch: ${sketchName}`, 'error');
        }
    }
    
    async loadTemplate(templateName) {
        try {
            const response = await fetch(`/api/template/${templateName}`);
            const data = await response.json();
            
            this.editor.setValue(data.content);
            this.currentSketch = 'Untitled.ino';
            this.updateTabName(this.currentSketch);
            this.addConsoleMessage(`Loaded template: ${templateName}`, 'info');
        } catch (error) {
            console.error('Failed to load template:', error);
            this.addConsoleMessage(`Failed to load template: ${templateName}`, 'error');
        }
    }
    
    showNewSketchModal() {
        document.getElementById('newSketchModal').classList.add('show');
        document.getElementById('newSketchName').focus();
    }
    
    hideModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
    }
    
    async createNewSketch() {
        const nameInput = document.getElementById('newSketchName');
        let sketchName = nameInput.value.trim();
        
        if (!sketchName) {
            alert('Please enter a sketch name');
            return;
        }
        
        if (!sketchName.endsWith('.ino')) {
            sketchName += '.ino';
        }
        
        // Create basic Arduino sketch
        const basicSketch = `// ${sketchName}
// Created: ${new Date().toLocaleDateString()}

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Your setup code here
}

void loop() {
  // Your main code here
}`;
        
        this.editor.setValue(basicSketch);
        this.currentSketch = sketchName;
        this.updateTabName(sketchName);
        this.hideModals();
        nameInput.value = '';
        
        this.addConsoleMessage(`Created new sketch: ${sketchName}`, 'success');
    }
    
    async saveCurrentSketch() {
        const content = this.editor.getValue();
        
        try {
            const formData = new FormData();
            formData.append('sketch_name', this.currentSketch);
            formData.append('content', content);
            
            const response = await fetch('/api/sketch/save', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.addConsoleMessage(`Saved: ${this.currentSketch}`, 'success');
                this.markSaved();
                await this.loadSketches(); // Refresh sketch list
            } else {
                this.addConsoleMessage(`Save failed: ${result.detail}`, 'error');
            }
        } catch (error) {
            console.error('Failed to save sketch:', error);
            this.addConsoleMessage('Failed to save sketch', 'error');
        }
    }
    
    async deleteSketch(sketchName) {
        try {
            const response = await fetch(`/api/sketch/${sketchName}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.addConsoleMessage(`Deleted: ${sketchName}`, 'success');
                await this.loadSketches();
            } else {
                const result = await response.json();
                this.addConsoleMessage(`Delete failed: ${result.detail}`, 'error');
            }
        } catch (error) {
            console.error('Failed to delete sketch:', error);
            this.addConsoleMessage('Failed to delete sketch', 'error');
        }
    }
    
    async compileSketch() {
        const board = document.getElementById('boardSelect').value;
        if (!board) {
            alert('Please select a board first');
            return;
        }
        
        // Save current sketch first
        await this.saveCurrentSketch();
        
        this.showLoading('Compiling...');
        this.addConsoleMessage('Starting compilation...', 'info');
        
        try {
            const formData = new FormData();
            formData.append('sketch_name', this.currentSketch);
            formData.append('board', board);
            
            const response = await fetch('/api/compile', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addConsoleMessage('Compilation successful!', 'success');
                if (result.output) {
                    this.addConsoleMessage(result.output, 'info');
                }
            } else {
                this.addConsoleMessage('Compilation failed!', 'error');
                if (result.error) {
                    this.addConsoleMessage(result.error, 'error');
                }
            }
        } catch (error) {
            console.error('Compilation error:', error);
            this.addConsoleMessage('Compilation error: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async uploadSketch() {
        const board = document.getElementById('boardSelect').value;
        const port = this.currentPort;
        
        if (!board) {
            alert('Please select a board first');
            return;
        }
        
        if (!port) {
            alert('Please select a port first');
            return;
        }
        
        this.showLoading('Uploading...');
        this.addConsoleMessage('Starting upload...', 'info');
        
        try {
            const formData = new FormData();
            formData.append('sketch_name', this.currentSketch);
            formData.append('board', board);
            formData.append('port', port);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addConsoleMessage('Upload successful!', 'success');
                if (result.output) {
                    this.addConsoleMessage(result.output, 'info');
                }
            } else {
                this.addConsoleMessage('Upload failed!', 'error');
                if (result.error) {
                    this.addConsoleMessage(result.error, 'error');
                }
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.addConsoleMessage('Upload error: ' + error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    toggleSerialMonitor() {
        this.switchOutputTab('serial');
    }
    
    toggleSerialConnection() {
        if (this.isSerialConnected) {
            this.disconnectSerial();
        } else {
            this.connectSerial();
        }
    }
    
    connectSerial() {
        if (!this.currentPort) {
            alert('Please select a port first');
            return;
        }
        
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/serial/${this.currentPort}`;
            
            this.serialSocket = new WebSocket(wsUrl);
            
            this.serialSocket.onopen = () => {
                this.isSerialConnected = true;
                this.updateSerialUI();
                this.addSerialMessage('Serial monitor connected', 'info');
            };
            
            this.serialSocket.onmessage = (event) => {
                this.addSerialMessage(event.data, 'data');
            };
            
            this.serialSocket.onerror = (error) => {
                console.error('Serial WebSocket error:', error);
                this.addSerialMessage('Serial connection error', 'error');
            };
            
            this.serialSocket.onclose = () => {
                this.isSerialConnected = false;
                this.updateSerialUI();
                this.addSerialMessage('Serial monitor disconnected', 'info');
            };
        } catch (error) {
            console.error('Failed to connect serial:', error);
            this.addSerialMessage('Failed to connect: ' + error.message, 'error');
        }
    }
    
    disconnectSerial() {
        if (this.serialSocket) {
            this.serialSocket.close();
            this.serialSocket = null;
        }
    }
    
    sendSerialData() {
        const input = document.getElementById('serialInput');
        const data = input.value.trim();
        
        if (data && this.serialSocket && this.isSerialConnected) {
            this.serialSocket.send('SEND:' + data);
            this.addSerialMessage('> ' + data, 'sent');
            input.value = '';
        }
    }
    
    updateSerialUI() {
        const connectBtn = document.getElementById('connectSerial');
        const serialInput = document.getElementById('serialInput');
        const sendBtn = document.getElementById('sendSerial');
        
        if (this.isSerialConnected) {
            connectBtn.textContent = 'Disconnect';
            connectBtn.className = 'btn-small btn-secondary';
            serialInput.disabled = false;
            sendBtn.disabled = false;
        } else {
            connectBtn.textContent = 'Connect';
            connectBtn.className = 'btn-small btn-primary';
            serialInput.disabled = true;
            sendBtn.disabled = true;
        }
    }
    
    async generateCode() {
        const prompt = document.getElementById('aiPrompt').value.trim();
        if (!prompt) {
            alert('Please enter a description of what you want to create');
            return;
        }
        
        this.showLoading('Generating code...');
        const responseDiv = document.getElementById('aiGenerateResponse');
        responseDiv.textContent = 'Generating Arduino code...';
        
        try {
            const formData = new FormData();
            formData.append('prompt', prompt);
            
            const response = await fetch('/api/ai/generate', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                responseDiv.textContent = result.code;
                
                // Add button to insert generated code
                const insertBtn = document.createElement('button');
                insertBtn.className = 'btn-primary';
                insertBtn.style.marginTop = '10px';
                insertBtn.textContent = 'Insert into Editor';
                insertBtn.onclick = () => {
                    this.editor.setValue(result.code);
                    this.addConsoleMessage('Generated code inserted', 'success');
                };
                
                responseDiv.appendChild(document.createElement('br'));
                responseDiv.appendChild(insertBtn);
            } else {
                responseDiv.textContent = `AI Error: ${result.error}`;
            }
        } catch (error) {
            console.error('AI generation error:', error);
            responseDiv.textContent = 'Failed to generate code: ' + error.message;
        } finally {
            this.hideLoading();
        }
    }
    
    async reviewCode() {
        const code = this.editor.getValue();
        if (!code.trim()) {
            alert('No code to review. Please write some Arduino code first.');
            return;
        }
        
        this.showLoading('Reviewing code...');
        const responseDiv = document.getElementById('aiReviewResponse');
        responseDiv.textContent = 'Analyzing your Arduino code...';
        
        try {
            const formData = new FormData();
            formData.append('code', code);
            
            const response = await fetch('/api/ai/review', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                responseDiv.textContent = result.review;
            } else {
                responseDiv.textContent = `AI Error: ${result.error}`;
            }
        } catch (error) {
            console.error('AI review error:', error);
            responseDiv.textContent = 'Failed to review code: ' + error.message;
        } finally {
            this.hideLoading();
        }
    }
    
    async checkOllamaStatus() {
        try {
            const response = await fetch('/api/ai/models');
            const result = await response.json();
            
            const statusEl = document.getElementById('ollamaStatus');
            
            if (result.success) {
                statusEl.className = 'status-indicator online';
                statusEl.innerHTML = '<i class="fas fa-circle"></i><span>Ollama: Connected</span>';
            } else {
                statusEl.className = 'status-indicator offline';
                statusEl.innerHTML = '<i class="fas fa-circle"></i><span>Ollama: Offline</span>';
            }
        } catch (error) {
            const statusEl = document.getElementById('ollamaStatus');
            statusEl.className = 'status-indicator offline';
            statusEl.innerHTML = '<i class="fas fa-circle"></i><span>Ollama: Error</span>';
        }
    }
    
    switchOutputTab(tabName) {
        // Update tabs
        document.querySelectorAll('.output-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Update content
        document.querySelectorAll('.output-section').forEach(section => {
            section.classList.toggle('active', section.id === `${tabName}Output`);
        });
    }
    
    switchAITab(tabName) {
        // Update tabs
        document.querySelectorAll('.ai-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Update content
        document.querySelectorAll('.ai-section').forEach(section => {
            section.classList.toggle('active', section.id === `${tabName}Panel`);
        });
    }
    
    updateTabName(name) {
        document.querySelector('.tab-name').textContent = name;
    }
    
    markUnsaved() {
        const tabName = document.querySelector('.tab-name');
        if (!tabName.textContent.endsWith('*')) {
            tabName.textContent += '*';
        }
    }
    
    markSaved() {
        const tabName = document.querySelector('.tab-name');
        tabName.textContent = tabName.textContent.replace('*', '');
    }
    
    addConsoleMessage(message, type = 'info') {
        const console = document.querySelector('.console-content');
        const messageEl = document.createElement('div');
        messageEl.className = `console-message ${type}`;
        messageEl.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        console.appendChild(messageEl);
        console.scrollTop = console.scrollHeight;
    }
    
    addSerialMessage(message, type = 'data') {
        const serial = document.querySelector('.serial-content');
        const messageEl = document.createElement('div');
        messageEl.className = `console-message ${type}`;
        
        if (type === 'data') {
            messageEl.textContent = message;
        } else {
            messageEl.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        }
        
        serial.appendChild(messageEl);
        serial.scrollTop = serial.scrollHeight;
    }
    
    clearConsole() {
        document.querySelector('.console-content').innerHTML = '';
    }
    
    clearSerial() {
        document.querySelector('.serial-content').innerHTML = '';
    }
    
    showLoading(message = 'Processing...') {
        const overlay = document.getElementById('loadingOverlay');
        const text = overlay.querySelector('p');
        text.textContent = message;
        overlay.classList.add('show');
    }
    
    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('show');
    }
}

// Initialize the Arduino IDE when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.arduinoIDE = new ArduinoIDE();
});

// Handle window resize for responsive layout
window.addEventListener('resize', () => {
    if (window.arduinoIDE && window.arduinoIDE.editor) {
        window.arduinoIDE.editor.refresh();
    }
});