#include <SDI12.h>

#define DATA_PIN 6
#define SENSE_TIMEOUT 1000 // Adjust this if necessary

SDI12 mySDI12(DATA_PIN);

void setup() {
  Serial.begin(9600);
  mySDI12.begin();
  delay(2000);

  for (char i = '0'; i <= '9'; i++) {
    mySDI12.sendCommand(String(i) + "I!");
    delay(SENSE_TIMEOUT);

    if (mySDI12.available() > 0) {
      String response = mySDI12.readStringUntil('\n');
      Serial.print("Sensor found at address ");
      Serial.print(i);
      Serial.print(", response: ");
      Serial.println(response);
      return;
    }
  }
  
  Serial.println("No sensor found.");
}

void loop() {
  // Nothing to do here
}
