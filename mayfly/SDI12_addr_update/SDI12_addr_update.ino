#include <SDI12.h>

// See: https://chat.openai.com/c/3c25945b-2ef1-458c-b576-05ef4b0d5482

struct SensorInfo
{
  char address;
  String identifier;
};

const int num_data_lines = 6;
const int sensor_pins[num_data_lines] = {4, 5, 6, 7, 10, 11};
SDI12 sdi12_objects[num_data_lines] = {SDI12(4), SDI12(5), SDI12(6), SDI12(7), SDI12(10), SDI12(11)};
bool sensor_connected[num_data_lines] = {true, true, false, false, false, false}; // Update this array with 'true' for connected sensors and 'false' for empty ports

SensorInfo sensor_mappings[num_data_lines];

String findSensorAddress(SDI12 &sdi12_object);
void assignSensorAddress(SDI12 &sdi12_object, int pin, int mapping_index);
char generateAddressFromIdentifier(const String &id_string);

void setup()
{
  Serial.begin(9600);
  delay(2000); // Wait for the serial connection to initialize

  for (int i = 0; i < num_data_lines; i++)
  {
    if (sensor_connected[i])
    {
      assignSensorAddress(sdi12_objects[i], sensor_pins[i], i);
    }
  }

  Serial.println("Address assignment completed");

  // Print the address mapping information
  for (int i = 0; i < num_data_lines; i++)
  {
    Serial.print("Address: ");
    Serial.print(sensor_mappings[i].address);
    Serial.print(" - Identifier: ");
    Serial.println(sensor_mappings[i].identifier);
  }
}

void loop()
{
  // Empty loop
}

String findSensorAddress(SDI12 &sdi12_object)
{
  sdi12_object.begin();
  delay(300);

  for (char address = '0'; address <= '9'; address++)
  {
    sdi12_object.sendCommand(String(address) + "I!");
    delay(300);

    if (sdi12_object.available() > 1)
    {
      String id_string = sdi12_object.readStringUntil('\n');
      id_string.trim();
      return address + ":" + id_string;
    }
  }

  for (char address = 'a'; address <= 'z'; address++)
  {
    sdi12_object.sendCommand(String(address) + "I!");
    delay(300);

    if (sdi12_object.available() > 1)
    {
      String id_string = sdi12_object.readStringUntil('\n');
      id_string.trim();
      return address + ":" + id_string;
    }
  }

  return ""; // Sensor not found
}

void assignSensorAddress(SDI12 &sdi12_object, int pin, int mapping_index)
{
  String found_address_id = findSensorAddress(sdi12_object);
  if (found_address_id.length() > 0)
  {
    char found_address = found_address_id.charAt(0);
    String id_string = found_address_id.substring(2);

    // Generate a new address based on the identifier
    char new_sensor_address = generateAddressFromIdentifier(id_string);

    // Assign the new address
    sdi12_object.sendCommand(String(found_address) + "A" + String(new_sensor_address) + "!");
    delay(300);

    // Verify that the address has changed
    sdi12_object.sendCommand(String(new_sensor_address) + "I!");
    delay(300);

    if (sdi12_object.available() > 1)
    {
      String response = sdi12_object.readStringUntil('\n');
      response.trim();
      if (response.endsWith(id_string))
      {
        Serial.print("Address ");
        Serial.print(found_address);
        Serial.print(" changed to ");
        Serial.println(new_sensor_address);

        // Store the address and identifier in the mapping
        sensor_mappings[mapping_index].address = new_sensor_address;
        sensor_mappings[mapping_index].identifier = id_string;
      }
      else
      {
        Serial.print("Failed to change address for ");
        Serial.println(id_string);
      }
    }
    else
    {
      Serial.print("Address change verification failed for ");
      Serial.println(id_string);
    }
  }
  else
  {
    Serial.println("No sensor found.");
  }
}

char generateAddressFromIdentifier(const String &id_string)
{
  // This is an example of generating an address using the sum of the ASCII values of the identifier
  int sum = 0;
  for (int i = 0; i < id_string.length(); i++)
  {
    sum += id_string.charAt(i);
  }

  // Map the sum to the range of valid SDI-12 addresses (ASCII '0' to '9' and 'a' to 'z')
  char new_address = '0' + (sum % 36);
  if (new_address > '9')
  {
    new_address += ('a' - '0' - 10);
  }

  // Ensure address uniqueness
  for (int i = 0; i < num_data_lines; i++)
  {
    if (sensor_mappings[i].address == new_address)
    {
      new_address++;
      if (new_address > 'z')
      {
        new_address = '0';
      }
      i = -1; // Restart the loop to check the new address against all sensors again
    }
  }

  return new_address;
}
