import serial.tools.list_ports
import serial
import time
import json
import logging

# Serial port detection
ports = list(serial.tools.list_ports.comports())
if len(ports) == 0:
    raise ValueError("No serial ports found")
elif len(ports) > 1:
    logging.warning("Multiple serial ports detected, using the first one")
serial_port = str(ports[0].device)

# Serial connection
ser = serial.Serial(serial_port, 9600, timeout=10)
time.sleep(2.5)


class Sensor:
    def __init__(self, id: str, address: str, analog: bool = False):
        self.id = id
        self.address = address
        self.analog = analog
        self.values = []

    def read(self, ser):
        if self.analog:
            return self.read_analog(ser)
        else:
            return self.read_digital(ser)

    def read_analog(self, ser):
        try:
            ser.write(bytes(self.address, "utf-8") + b"M8!")
            sdi_12_line = ser.readline()
            sdi_12_line = ser.readline()
            ser.write(bytes(self.address, "utf-8") + b"D0!")
            sdi_12_line = sdi_12_line[:-2]
            sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]
            return {self.id + str(i): value for i, value in enumerate(sensor_values)}
        except Exception as e:
            logging.error(
                f"An error occurred while reading analog data: {e}", exc_info=True
            )
            return {}

    def read_digital(self, ser):
        try:
            ser.write(bytes(self.address, "utf-8") + b"M!")
            sdi_12_line = ser.readline()
            sdi_12_line = ser.readline()
            ser.write(bytes(self.address, "utf-8") + b"D0!")
            sdi_12_line = sdi_12_line[:-2]
            sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]
            return {self.id: value for value in sensor_values}
        except Exception as e:
            logging.error(
                f"An error occurred while reading digital data: {e}", exc_info=True
            )
            return {}


# Load sensor data from a JSON file
with open("./sensor_profiles.json") as f:
    sensor_profiles = json.load(f)

# Initialize sensor objects
sensors = []
for profile in sensor_profiles:
    sensor_id = profile["sensor_id"]
    address = profile["SDI-12 Address"]
    analog = bool(profile["Analog address"])
    sensors.append(Sensor(sensor_id, address, analog))
