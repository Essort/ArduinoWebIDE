
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
