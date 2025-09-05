/*
  Arduino LED Pattern Demo
  This sketch creates a beautiful LED pattern using the built-in LED
  
  Circuit:
  - Built-in LED on pin 13 (no external components needed)
  
  Created: 2025-01-05
  By: Arduino Web IDE Demo
*/

int ledPin = 13;        // Built-in LED pin
int brightness = 0;     // Current brightness level
int fadeAmount = 5;     // Amount to fade each step

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize the LED pin as output
  pinMode(ledPin, OUTPUT);
  
  Serial.println("Arduino LED Pattern Demo Started!");
  Serial.println("Watch the built-in LED for a breathing effect.");
}

void loop() {
  // Set LED brightness using PWM
  analogWrite(ledPin, brightness);
  
  // Print current brightness to serial monitor
  Serial.print("LED Brightness: ");
  Serial.println(brightness);
  
  // Change brightness for next iteration
  brightness = brightness + fadeAmount;
  
  // Reverse fade direction at the ends
  if (brightness <= 0 || brightness >= 255) {
    fadeAmount = -fadeAmount;
  }
  
  // Wait for 30 milliseconds to create smooth fading
  delay(30);
}