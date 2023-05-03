#include <SDI12.h>
#define DATA_PIN 4
#define SENSE_TIMEOUT 1000 // Adjust this if necessary
SDI12 mySDI12(DATA_PIN);
void setup() {
  Serial.begin(1200); // Set baud rate to 1200
  mySDI12.begin();
  delay(2000);
  bool sensorFound = false; // Flag variable
  char i = '0'; // Address variable
  while (i <= 'z') { // End of address range
    
    char command[3]; // Char array for command
    command[0] = i; // Address
    command[1] = 'I'; // Command
    command[2] = '!'; // Terminator
    mySDI12.sendCommand(command); // Send command
    delay(SENSE_TIMEOUT);
    if (mySDI12.available() > 0) {
      char response[20]; // Char array for response
      int index = 0; // Index variable
      while (mySDI12.available()) {
        char c = mySDI12.read(); // Read character
        if (c == '\n' || c == '\r') break; // Break on newline or carriage return
        if (c == '?') { // Check for error
          Serial.print("Error at address ");
          Serial.println(i);
          break;
        }
        response[index] = c; // Store character in response array
        index++; // Increment index
      }
      response[index] = '\0'; // Add null terminator to response array
      Serial.print("Sensor found at address ");
      Serial.print(i);
      Serial.print(", response: ");
      Serial.println(response);
      sensorFound = true; // Set flag to true
    }
    i++; // Increment address
    if (i == ':') i = 'A'; // Skip invalid characters
    if (i == '[') i = 'a'; // Skip invalid characters
  }
  if (!sensorFound) { // Check flag
    Serial.println("No sensor found.");
  }
}
void loop() {
  // Nothing to do here
}