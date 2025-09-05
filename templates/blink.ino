
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
