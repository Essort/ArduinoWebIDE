# Arduino Web IDE

A comprehensive web-based Arduino development environment featuring a modern code editor, Arduino CLI integration, real-time serial monitoring, and AI-powered code assistance.

## Features

### 🔧 Core IDE Features
- **Modern Code Editor**: CodeMirror-based editor with Arduino C/C++ syntax highlighting
- **Arduino CLI Integration**: Compile and upload sketches directly to your Arduino boards
- **Real-time Serial Monitor**: WebSocket-based serial communication with your Arduino
- **File Management**: Create, save, load, and delete Arduino sketches
- **Project Templates**: Pre-built templates for common Arduino projects
- **Responsive Design**: Professional dark theme optimized for coding

### 🤖 AI Assistant (Ollama Integration)
- **Code Generation**: Generate Arduino code from natural language descriptions
- **Code Review**: AI-powered analysis for bugs, optimizations, and best practices
- **Smart Suggestions**: Context-aware code completion and recommendations
- **Local AI**: Runs entirely on your machine via Ollama (no cloud required)

### 📟 Hardware Support
- Arduino Uno
- Arduino Nano
- Arduino Mega 2560
- ESP32 Dev Module
- ESP8266 NodeMCU

## Quick Start

### Prerequisites

1. **Python 3.7+**
   ```bash
   python3 --version
   ```

2. **Arduino CLI** (for compilation/upload)
   ```bash
   # Install Arduino CLI
   curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
   # Add to PATH
   export PATH=$PATH:~/bin
   ```

3. **Ollama** (for AI features - optional)
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull recommended model
   ollama pull codellama
   ```

### Installation

1. **Clone or Download** this repository

2. **Make start script executable**:
   ```bash
   chmod +x start.sh
   ```

3. **Run the startup script**:
   ```bash
   ./start.sh
   ```

   The script will:
   - Install Python dependencies
   - Check for Arduino CLI
   - Verify Ollama service
   - Start the web server

4. **Open your browser** to `http://localhost:8000`

## Manual Installation

If you prefer to install manually:

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Start the server
python3 main.py
```

## Usage Guide

### Getting Started

1. **Select your Arduino board** from the dropdown in the toolbar
2. **Choose your serial port** (auto-detected)
3. **Start coding** in the editor or load a template
4. **Verify your code** with the compile button (✓)
5. **Upload to your Arduino** with the upload button (↑)

### File Management

- **New Sketch**: Click the "+" button in the Files panel
- **Save Sketch**: Ctrl+S or click the save button
- **Load Sketch**: Click any sketch in the "My Sketches" list
- **Load Template**: Click any template in the "Templates" list
- **Delete Sketch**: Right-click on a sketch and confirm deletion

### Serial Monitor

1. Click "Serial Monitor" in the toolbar or switch to the "Serial Monitor" tab
2. Select your baud rate (default: 9600)
3. Click "Connect" to start monitoring
4. Type messages in the input field and press Enter to send

### AI Assistant

#### Code Generation
1. Switch to the "Generate" tab in the AI panel
2. Describe what you want to create (e.g., "Blink LED on pin 13")
3. Click "Generate Code"
4. Review the generated code and click "Insert into Editor" if satisfied

#### Code Review
1. Write your Arduino code in the editor
2. Switch to the "Review" tab in the AI panel
3. Click "Review Current Code"
4. Review the AI analysis for bugs, improvements, and best practices

## Keyboard Shortcuts

- **Ctrl+S**: Save current sketch
- **Ctrl+R**: Compile/Verify sketch
- **Ctrl+U**: Upload sketch
- **Ctrl+Space**: Trigger code completion
- **F9**: Compile sketch
- **F10**: Upload sketch

## Configuration

### Arduino CLI Setup

After installing Arduino CLI, you may need to install board packages:

```bash
# Update the package index
arduino-cli core update-index

# Install Arduino AVR boards (Uno, Nano, Mega)
arduino-cli core install arduino:avr

# Install ESP32 boards
arduino-cli core install esp32:esp32 --additional-urls https://dl.espressif.com/dl/package_esp32_index.json

# Install ESP8266 boards
arduino-cli core install esp8266:esp8266 --additional-urls https://arduino.esp8266.com/stable/package_esp8266com_index.json
```

### Ollama Models

Recommended models for Arduino development:

```bash
# General code generation
ollama pull codellama

# Instruction-tuned for better responses
ollama pull codellama:7b-instruct

# Larger model for better quality (requires more RAM)
ollama pull codellama:13b-instruct
```

## API Documentation

The web IDE provides a REST API for integration:

### Sketches
- `GET /api/sketches` - List all sketches
- `GET /api/sketch/{name}` - Get sketch content
- `POST /api/sketch/save` - Save a sketch
- `DELETE /api/sketch/{name}` - Delete a sketch

### Arduino Operations
- `GET /api/boards` - List supported boards
- `GET /api/ports` - List available serial ports
- `POST /api/compile` - Compile a sketch
- `POST /api/upload` - Upload a sketch to board

### AI Features
- `POST /api/ai/generate` - Generate code from prompt
- `POST /api/ai/review` - Review code for improvements
- `GET /api/ai/models` - List available Ollama models

### WebSocket
- `WS /ws/serial/{port}` - Real-time serial communication

## Project Structure

```
arduino-web-ide/
├── main.py                 # FastAPI server application
├── requirements.txt        # Python dependencies
├── start.sh               # Startup script
├── static/                # Frontend assets
│   ├── index.html         # Main web interface
│   ├── style.css          # Dark theme styling
│   └── app.js             # JavaScript application
├── sketches/              # User Arduino sketches
├── templates/             # Arduino project templates
├── libraries/             # Arduino libraries
└── uploads/               # Temporary compilation files
```

## Troubleshooting

### Arduino CLI Issues

**Problem**: "arduino-cli: command not found"

**Solution**: Ensure Arduino CLI is installed and in your PATH:
```bash
which arduino-cli
echo $PATH
```

**Problem**: "Board not supported"

**Solution**: Install the required board package:
```bash
arduino-cli core search esp32
arduino-cli core install esp32:esp32
```

### Serial Connection Issues

**Problem**: "Permission denied" when accessing serial port

**Solution**: Add your user to the dialout group (Linux/macOS):
```bash
sudo usermod -a -G dialout $USER
# Log out and log back in
```

### Ollama AI Issues

**Problem**: "Ollama service not available"

**Solution**: Start Ollama service:
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

**Problem**: "Model not found"

**Solution**: Pull the required model:
```bash
ollama pull codellama
```

### Port Access Issues

**Problem**: Can't access http://localhost:8000

**Solution**: Check if port is already in use:
```bash
lsof -i :8000
# Kill any conflicting processes
kill -9 <PID>
```

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions:

1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information

## Acknowledgments

- **Arduino CLI**: Official Arduino command-line interface
- **CodeMirror**: Versatile text editor for the browser
- **FastAPI**: Modern web framework for building APIs
- **Ollama**: Local LLM runner for AI features
- **Arduino Community**: For the extensive libraries and examples
