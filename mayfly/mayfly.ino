#include <Adafruit_FONA.h>
#include <SDI12.h>
#include <LowPower.h>
#include <ArduinoJson.h>
#include <SD.h>

// Sensor and communication settings
const char sensor_addresses[] = {'0', '1', '2', '3', '4', '5'}; // Assign addresses for your 6 SDI-12 sensors
const uint8_t num_sensors = sizeof(sensor_addresses);
float sensor_data[num_sensors];
const uint8_t data_pin = 7;
SDI12 sdi12(data_pin);

// FONA settings
#define FONA_RX 6
#define FONA_TX 5
#define FONA_RST 4
Adafruit_FONA_3G fona = Adafruit_FONA_3G(FONA_RST);
#define FONA_SERIAL Serial1

// Sleep settings
#define SLEEP_DURATION 2  // Sleep duration in 8-second intervals
#define SLEEP_8S 1         // Sleep for 8 seconds

// BigQuery settings
String project_id = "your_project_id";
String dataset_id = "your_dataset_id";
String table_id = "your_table_id";
String api_key = "your_api_key";

// SD card settings
const int chipSelect = 10;  // Mayfly's SD card CS pin

void setup() {
  Serial.begin(115200);
  
  // SDI-12 sensor initialization
  sdi12.begin();
  delay(2000);
  
  // FONA module initialization
  digitalWrite(FONA_RST, HIGH);
  delay(1000);
  
  if (!fona.begin(FONA_SERIAL)) {
    Serial.println("Couldn't find FONA");
    while (1);
  }
  
  // SD card initialization
  if (!SD.begin(chipSelect)) {
    Serial.println("SD card initialization failed!");
    return;
  }
}

void loop() {
  readSensors();
  
  int retries = 3;
  while (retries > 0) {
    if (sendDataToBigQuery()) {
      break;
    }
    retries--;
  }
  
  //goToSleep();
}

void readSensors() {
  for (unsigned int i = 0; i < num_sensors; i++) {
    String sdi_command = String(sensor_addresses[i]) + "M!";
    sdi12.sendCommand(sdi_command);
    delay(30);
    sdi12.read();
    int num_values = sdi12.available(); // Get number of values
    if (num_values == 1) { // Check if it matches expected number. This is a potential source of error. Chech documentation for expected value
      float value = sdi12.parseFloat(0); // Parse value
      sensor_data[i] = value;
    } else {
      sensor_data[i] = -9999.0; // Error value
    }
  }
}


bool sendDataToBigQuery() {
  int16_t statuscode;
  uint16_t length;
  
  String jsonPayload = createJsonPayload();
  
  // Save data to SD card
  saveDataToSDCard(jsonPayload);

  if (fona.enableGPS(true)) {
    if (fona.HTTP_POST_start(project_id.c_str(), F("application/json"), (uint8_t *)jsonPayload.c_str(), jsonPayload.length(), &statuscode, &length)) {
      while (length) {
        while (fona.available()) {
          char c = fona.read();
          Serial.write(c);
          length--;
          if (!length) break;
        }
      }
      Serial.println();
      fona.HTTP_POST_end();
      fona.enableGPS(false);
      return true;
    } else {
      // Disable SSL and GPRS connections in case of a failed HTTP POST
      fona.enableGPS(false);
      return false;
    }
  } else {
    Serial.println("Failed to enable GPS!");
    return false;
  }
}


String createJsonPayload() {
  StaticJsonDocument<256> doc;
  JsonObject row = doc.createNestedObject();
  JsonObject json = row.createNestedObject("json");
  
  for (uint8_t i = 0; i < num_sensors; i++) {
    json["sensor_" + String(i + 1)] = sensor_data[i];
  }
  String payload;
  serializeJson(doc, payload);
  return payload;
}

void saveDataToSDCard(const String& data) {
  File dataFile = SD.open("datalog.txt", FILE_WRITE);

  if (dataFile) {
    dataFile.println(data);
    dataFile.close();
    Serial.println("Data saved to SD card.");
  } else {
    Serial.println("Error opening datalog.txt");
  }
}

void goToSleep() {
  for (uint8_t i = 0; i < SLEEP_DURATION; i++) {
    LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
  }
}

