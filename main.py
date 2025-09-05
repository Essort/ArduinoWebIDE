#!/usr/bin/env python3
"""
Arduino Web IDE with AI Integration
Main FastAPI application server
"""

import os
import json
import socket
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

import uvicorn
from uvicorn.config import Config
from uvicorn.server import Server
import signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import serial
import serial.tools.list_ports
import psutil
import requests
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Arduino Web IDE", description="Web-based Arduino IDE with AI integration")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project directories
BASE_DIR = Path(__file__).parent
SKETCHES_DIR = BASE_DIR / "sketches"
LIBRARIES_DIR = BASE_DIR / "libraries"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"

# Create directories if they don't exist
for dir_path in [SKETCHES_DIR, LIBRARIES_DIR, TEMPLATES_DIR, STATIC_DIR, UPLOADS_DIR]:
    dir_path.mkdir(exist_ok=True)

# Active serial connections
active_connections: Dict[str, WebSocket] = {}
serial_connections: Dict[str, serial.Serial] = {}

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

async def startup_event():
    """Initialize the application"""
    print("Starting Arduino Web IDE...")
    
    # Create default sketch templates
    await create_default_templates()
    
    # Check Arduino CLI installation
    arduino_cli_status = await check_arduino_cli()
    if not arduino_cli_status:
        print("Arduino CLI not found. Please install Arduino CLI for full functionality.")
    
    print("Arduino Web IDE started successfully!")

# Add startup event handler
app.add_event_handler("startup", startup_event)

async def create_default_templates():
    """Create default Arduino sketch templates"""
    templates = {
        "blink.ino": '''
// Arduino Blink Example
// Blinks an LED connected to pin 13

void setup() {
  // Initialize digital pin 13 as an output
  pinMode(13, OUTPUT);
}

void loop() {
  digitalWrite(13, HIGH);   // Turn the LED on
  delay(1000);              // Wait for a second
  digitalWrite(13, LOW);    // Turn the LED off
  delay(1000);              // Wait for a second
}
''',
        "serial_hello.ino": '''
// Arduino Serial Hello World
// Sends "Hello World!" to serial monitor

void setup() {
  // Initialize serial communication at 9600 baud
  Serial.begin(9600);
}

void loop() {
  Serial.println("Hello World!");
  delay(1000);
}
''',
        "analog_read.ino": '''
// Arduino Analog Read Example
// Reads analog input and prints to serial

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(A0);
  Serial.print("Sensor Value: ");
  Serial.println(sensorValue);
  delay(100);
}
''',
        "servo_control.ino": '''
// Arduino Servo Control Example
// Controls a servo motor

#include <Servo.h>

Servo myservo;
int pos = 0;

void setup() {
  myservo.attach(9);  // Attaches the servo on pin 9
}

void loop() {
  for (pos = 0; pos <= 180; pos += 1) {
    myservo.write(pos);
    delay(15);
  }
  for (pos = 180; pos >= 0; pos -= 1) {
    myservo.write(pos);
    delay(15);
  }
}
''',
        "esp32_wifi.ino": '''
// ESP32 WiFi Connection Example
// Connects to WiFi and prints IP address

#include <WiFi.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

void setup() {
  Serial.begin(115200);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("Connected to WiFi!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Your code here
}
'''
    }
    
    for filename, content in templates.items():
        template_path = TEMPLATES_DIR / filename
        if not template_path.exists():
            async with aiofiles.open(template_path, 'w') as f:
                await f.write(content)

async def check_arduino_cli() -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_check)

def _sync_check() -> bool:
    try:
        p = subprocess.run(["arduino-cli", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return p.returncode == 0
    except (FileNotFoundError, PermissionError, OSError):
        return False

async def check_arduino_cli_linux() -> bool:
    """Check if Arduino CLI is installed"""
    try:
        result = await asyncio.create_subprocess_exec(
            "arduino-cli", "version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await result.communicate()
        return result.returncode == 0
    except (FileNotFoundError, PermissionError, OSError):
        return False

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main Arduino IDE interface"""
    html_file = STATIC_DIR / "index.html"
    if html_file.exists():
        async with aiofiles.open(html_file, 'r') as f:
            content = await f.read()
        return HTMLResponse(content=content)
    else:
        return HTMLResponse(content="<h1>Arduino Web IDE</h1><p>Loading...</p>")

@app.get("/api/boards")
async def get_boards():
    """Get list of supported Arduino boards"""
    boards = {
        "arduino:avr:nano": "Arduino Nano",
        "arduino:avr:uno": "Arduino Uno", 
        "arduino:avr:mega": "Arduino Mega 2560",
        "esp32:esp32:esp32": "ESP32 Dev Module",
        "esp32:esp32:esp32s3": "ESP32-S3 Module",
        "esp8266:esp8266:nodemcuv2": "ESP8266 NodeMCU"
    }
    return {"boards": boards}

@app.get("/api/ports")
async def get_serial_ports():
    """Get list of available serial ports"""
    ports = []
    for port in serial.tools.list_ports.comports():
        ports.append({
            "device": port.device,
            "name": port.name,
            "description": port.description,
            "hwid": port.hwid
        })
    return {"ports": ports}

@app.get("/api/sketches")
async def get_sketches():
    """Get list of Arduino sketches"""
    sketches = []
    for sketch_path in SKETCHES_DIR.glob("*.ino"):
        sketches.append({
            "name": sketch_path.name,
            "path": str(sketch_path),
            "modified": os.path.getmtime(sketch_path)
        })
    return {"sketches": sketches}

@app.get("/api/templates")
async def get_templates():
    """Get list of Arduino sketch templates"""
    templates = []
    for template_path in TEMPLATES_DIR.glob("*.ino"):
        templates.append({
            "name": template_path.name,
            "path": str(template_path)
        })
    return {"templates": templates}

@app.get("/api/sketch/{sketch_name}")
async def get_sketch(sketch_name: str):
    sketch_path = SKETCHES_DIR / sketch_name
    if not sketch_path.exists():
        raise HTTPException(status_code=404, detail="Sketch not found")

    async with aiofiles.open(sketch_path, 'r', encoding='utf-8') as f:
        content = await f.read()

    return {"name": sketch_name, "content": content}


@app.get("/api/template/{template_name}")
async def get_template(template_name: str):
    """Get content of a specific template"""
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    async with aiofiles.open(template_path, 'r', encoding='utf-8') as f:
        content = await f.read()
    
    return {"name": template_name, "content": content}

@app.post("/api/sketch/save")
async def save_sketch(sketch_name: str = Form(...), content: str = Form(...)):
    if not sketch_name.endswith('.ino'):
        sketch_name += '.ino'

    content = content.replace('\r\n', '\n').replace('\r', '\n')

    sketch_path = SKETCHES_DIR / sketch_name

    async with aiofiles.open(sketch_path, 'w', encoding='utf-8') as f:
        await f.write(content)

    return {"message": f"Sketch '{sketch_name}' saved successfully"}

@app.delete("/api/sketch/{sketch_name}")
async def delete_sketch(sketch_name: str):
    """Delete an Arduino sketch"""
    sketch_path = SKETCHES_DIR / sketch_name
    if not sketch_path.exists():
        raise HTTPException(status_code=404, detail="Sketch not found")
    
    os.remove(sketch_path)
    return {"message": f"Sketch '{sketch_name}' deleted successfully"}

def _run_compile_sync(cmd, cwd=None):
    
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            check=False,
            text=True  # azonnal str-ként kapod az outputot
        )
        return proc.returncode, proc.stdout, proc.stderr
    except (FileNotFoundError, PermissionError, OSError) as e:
        # egységes hibaválasz, amit az async hívó kezel
        return 127, "", str(e)

@app.post("/api/compile")
async def compile_sketch(sketch_name: str = Form(...), board: str = Form(...)):
    """Compile an Arduino sketch"""
    sketch_path = SKETCHES_DIR / sketch_name

    if not sketch_path.exists():
        raise HTTPException(status_code=404, detail="Sketch not found")

    try:
        # Create temporary directory for compilation
        compile_dir = UPLOADS_DIR / f"compile_{sketch_name}_{datetime.now().timestamp()}"
        compile_dir.mkdir(exist_ok=True)

        # Ensure the main .ino filename matches the compile_dir name
        main_ino_name = compile_dir.name + ".ino"
        compile_main_ino = compile_dir / main_ino_name

        # Read original sketch (can be .ino or a file within a sketch folder)
        async with aiofiles.open(sketch_path, 'r', encoding='utf-8') as src:
            content = await src.read()

        async with aiofiles.open(compile_main_ino, 'w', encoding='utf-8') as dst:
            await dst.write(content)

		# Run Arduino CLI: pass the sketch folder (compile_dir)
        cmd = [
            "arduino-cli", "compile",
            "--fqbn", board,
            "--output-dir", str(compile_dir),
            str(compile_dir)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return {
                "success": True,
                "message": "Compilation successful",
                "output": stdout.decode('utf-8'),
                "compile_dir": str(compile_dir)
            }
        else:
            return {
                "success": False,
                "message": "Compilation failed",
                "error": stderr.decode('utf-8')
            }

    except Exception as e:
        return {
            "success": False,
            "message": "Compilation error",
            "error": str(e)
        }

@app.post("/api/upload")
async def upload_sketch(
    sketch_name: str = Form(...), 
    board: str = Form(...), 
    port: str = Form(...)
):
    """Upload compiled sketch to Arduino board"""
    sketch_path = SKETCHES_DIR / sketch_name
    if not sketch_path.exists():
        raise HTTPException(status_code=404, detail="Sketch not found")
    
    try:


        # First compile the sketch
        compile_result = await compile_sketch(sketch_name, board)

        if not compile_result["success"]:
            return compile_result

        sketch_path = compile_result["compile_dir"]
        
        # Upload to board
        cmd = [
            "arduino-cli", "upload",
            "--fqbn", board,
            "--port", port,
            str(sketch_path)
        ]
        

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {
                "success": True,
                "message": "Upload successful",
                "output": stdout.decode('utf-8')
            }
        else:
            return {
                "success": False,
                "message": "Upload failed",
                "error": stderr.decode('utf-8')
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": "Upload error",
            "error": str(e)
        }

# WebSocket endpoint for serial monitoring
@app.websocket("/ws/serial/{port}")
async def websocket_serial(websocket: WebSocket, port: str):
    """WebSocket endpoint for real-time serial communication"""
    await manager.connect(websocket)
    
    try:
        # Open serial connection
        if port in serial_connections:
            serial_connections[port].close()
        
        ser = serial.Serial(port, 9600, timeout=1)
        serial_connections[port] = ser
        
        # Background task to read from serial
        async def read_serial():
            while True:
                try:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode('utf-8').strip()
                        await manager.send_personal_message(data, websocket)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    await manager.send_personal_message(f"Error reading serial: {str(e)}", websocket)
                    break
        
        # Start serial reading task
        read_task = asyncio.create_task(read_serial())
        
        # Handle incoming messages (commands to send to serial)
        while True:
            data = await websocket.receive_text()
            if data.startswith('SEND:'):
                command = data[5:]
                ser.write((command + '\n').encode('utf-8'))
            elif data.startswith('BAUD:'):
                baud_rate = int(data[5:])
                ser.baudrate = baud_rate
                await manager.send_personal_message(f"Baud rate set to {baud_rate}", websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        if port in serial_connections:
            serial_connections[port].close()
            del serial_connections[port]
    except Exception as e:
        await manager.send_personal_message(f"Serial connection error: {str(e)}", websocket)
        manager.disconnect(websocket)
        if port in serial_connections:
            serial_connections[port].close()
            del serial_connections[port]

# Ollama AI Integration
@app.post("/api/ai/generate")
async def ai_generate_code(prompt: str = Form(...)):
    """Generate Arduino code using Ollama AI"""
    try:
        # Check if Ollama is running
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            return {"success": False, "error": "Ollama service not available"}
        
        # Prepare the prompt for Arduino code generation
        arduino_prompt = f"""
You are an Arduino programming expert. Generate Arduino C/C++ code for the following request:

{prompt}

Requirements:
- Provide complete, working Arduino code
- Include necessary libraries and setup
- Add helpful comments
- Follow Arduino best practices
- Make the code production-ready

Arduino Code:
"""
        
        # Send request to Ollama
        ollama_data = {
            "model": "codellama",  # Default to CodeLlama, user can change
            "prompt": arduino_prompt,
            "stream": False
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_code = result.get("response", "")
            
            return {
                "success": True,
                "code": generated_code,
                "prompt": prompt
            }
        else:
            return {
                "success": False,
                "error": f"Ollama API error: {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection to Ollama failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI generation error: {str(e)}"
        }

@app.post("/api/ai/review")
async def ai_review_code(code: str = Form(...)):
    """Review Arduino code using Ollama AI"""
    try:
        # Check if Ollama is running
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            return {"success": False, "error": "Ollama service not available"}
        
        # Prepare the prompt for code review
        review_prompt = f"""
You are an Arduino programming expert. Please review the following Arduino code and provide:

1. Code quality assessment
2. Potential bugs or issues
3. Performance optimizations
4. Best practice recommendations
5. Security considerations (if applicable)

Arduino Code to Review:
```cpp
{code}
```

Please provide a detailed review:
"""
        
        # Send request to Ollama
        ollama_data = {
            "model": "codellama",
            "prompt": review_prompt,
            "stream": False
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=ollama_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            review_result = result.get("response", "")
            
            return {
                "success": True,
                "review": review_result
            }
        else:
            return {
                "success": False,
                "error": f"Ollama API error: {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Connection to Ollama failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI review error: {str(e)}"
        }

@app.get("/api/ai/models")
async def get_ollama_models():
    """Get list of available Ollama models"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {"success": True, "models": models}
        else:
            return {"success": False, "error": "Failed to fetch models"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_reuse_socket(host: str, port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(2048)
    s.setblocking(False)
    return s

async def run_server(host="127.0.0.1", port=8001):
    sock = create_reuse_socket(host, port)
    config = Config("main:app", host=host, port=port, log_level="info", reload=False)
    server = Server(config=config)
    # serve() visszatér, amikor server.shutdown() meghívódik.
    await server.serve(sockets=[sock])

def main():
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        # Ctrl+C esetén tisztán kilép
        pass

if __name__ == "__main__":
    main()