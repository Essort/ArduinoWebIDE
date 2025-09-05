# Arduino Web IDE Setup Guide

## Prerequisites Installation

### 1. Python 3.7+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

**macOS:**
```bash
# Using Homebrew
brew install python3

# Or download from python.org
```

**Windows:**
```bash
# Download from python.org and install
# Make sure to check "Add Python to PATH"
```

### 2. Arduino CLI

**Linux/macOS:**
```bash
# Download and install Arduino CLI
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=~/bin sh

# Add to PATH
echo 'export PATH=$PATH:~/bin' >> ~/.bashrc
source ~/.bashrc

# Verify installation
arduino-cli version
```

**Windows:**
```bash
# Download the Windows installer from:
# https://github.com/arduino/arduino-cli/releases
# Run the installer and add to PATH
```

### 3. Arduino Board Packages

```bash
# Initialize Arduino CLI
arduino-cli config init

# Update package index
arduino-cli core update-index

# Install Arduino AVR boards (Uno, Nano, Mega)
arduino-cli core install arduino:avr

# Install ESP32 boards
arduino-cli config add board_manager.additional_urls https://dl.espressif.com/dl/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32

# Install ESP8266 boards
arduino-cli config add board_manager.additional_urls https://arduino.esp8266.com/stable/package_esp8266com_index.json
arduino-cli core update-index
arduino-cli core install esp8266:esp8266
```

### 4. Ollama (Optional - for AI features)

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
# Download from https://ollama.ai/download
# Or using Homebrew
brew install ollama
```

**Windows:**
```bash
# Download the Windows installer from:
# https://ollama.ai/download
```

**Install recommended models:**
```bash
# Start Ollama service
ollama serve

# In another terminal, install models
ollama pull codellama
ollama pull codellama:7b-instruct
```

## Arduino Web IDE Installation

### Quick Start (Recommended)

1. **Download/Clone the project**

2. **Run the startup script:**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. **Open http://localhost:8000 in your browser**

### Manual Installation

1. **Install Python dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python3 main.py
   ```

3. **Access the IDE at http://localhost:8000**

## Verification Steps

### 1. Test Arduino CLI
```bash
# Check version
arduino-cli version

# List installed boards
arduino-cli board listall

# List connected devices
arduino-cli board list
```

### 2. Test Serial Ports
```bash
# List available ports (Linux/macOS)
ls /dev/tty*

# Windows
mode
```

### 3. Test Ollama (if installed)
```bash
# Check if service is running
curl http://localhost:11434/api/tags

# List installed models
ollama list
```

## Common Issues and Solutions

### Permission Issues (Linux/macOS)

**Serial Port Access:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in, then verify
groups
```

### Arduino CLI Issues

**Missing Board Packages:**
```bash
# Search for boards
arduino-cli core search esp32

# Install specific board
arduino-cli core install esp32:esp32
```

**Config Issues:**
```bash
# Reset Arduino CLI configuration
rm -rf ~/.arduino15
arduino-cli config init
```

### Port Conflicts

**Port 8000 in use:**
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or run on different port
python3 main.py --port 8080
```

### Ollama Issues

**Service not starting:**
```bash
# Check Ollama logs
ollama logs

# Restart service
ollama serve
```

**Model download issues:**
```bash
# Clear cache and retry
ollama rm codellama
ollama pull codellama
```

## Development Environment

### For Development/Modification

```bash
# Install additional dev dependencies
pip3 install uvicorn[standard] watchdog

# Run in development mode with auto-reload
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### File Structure for Development

```
arduino-web-ide/
├── main.py                 # Main FastAPI application
├── static/
│   ├── index.html         # Web interface
│   ├── style.css          # Styling
│   └── app.js             # Frontend logic
├── sketches/              # User sketches (auto-created)
├── templates/             # Project templates (auto-created)
└── uploads/               # Temp files (auto-created)
```

## Next Steps

1. **Connect your Arduino board** via USB
2. **Open the web IDE** at http://localhost:8000
3. **Select your board** from the dropdown
4. **Choose your serial port**
5. **Start coding!**

For detailed usage instructions, see the main README.md file.