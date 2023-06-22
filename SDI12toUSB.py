import serial.tools.list_ports
import serial
import time
from datetime import datetime, timedelta
import json
import gcloud_functions as gcloud
import logging

# Configure logging
logging.basicConfig(
    filename="SDI12toUSB.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logging.getLogger("google").setLevel(logging.WARNING)

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

# BigQuery and Google Cloud Storage configurations
project_id = "apt-rite-378417"
dataset_id = "loggertest1"
table_id = "SDI12Test2"


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
        ser.write(bytes(self.address, "utf-8") + b"M8!")
        sdi_12_line = ser.readline()
        sdi_12_line = ser.readline()
        ser.write(bytes(self.address, "utf-8") + b"D0!")
        sdi_12_line = sdi_12_line[:-2]
        sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]

        # Return the dictionary of sensor values with keys as the sensor_id followed by analog address
        return {self.id + str(i): value for i, value in enumerate(sensor_values)}

    def read_digital(self, ser):
        # Send the measurement command to the sensor
        ser.write(bytes(self.address, "utf-8") + b"M!")
        # Read and discard the first line of the response
        sdi_12_line = ser.readline()
        # Read and discard the second line of the response
        sdi_12_line = ser.readline()
        # Send the data command to the sensor
        ser.write(bytes(self.address, "utf-8") + b"D0!")
        # Read the third line of the response, which contains the data
        sdi_12_line = ser.readline()
        # Remove the newline characters from the end of the line
        sdi_12_line = sdi_12_line[:-2]
        # Split the response into a list of values, excluding the first element (sensor address)
        sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]
        # Return the list of cleaned sensor values
        return {self.id: value for value in sensor_values}


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

last_upload_time = datetime.now()
upload_interval = 60  # In seconds, update according to your requirement
sampling_interval = 1  # In seconds, update according to your requirement

try:
    while True:
        sensor_data = {"Datetime": datetime.now().isoformat()}
        for sensor in sensors:
            sensor_data.update(sensor.read(ser))

        # Save sensor data to a file
        with open("./sensor_data.json", "a") as f:
            json.dump(sensor_data, f)
            f.write("\n")

        # Push sensor data to BigQuery and Google Cloud Storage
        if (datetime.now() - last_upload_time).total_seconds() >= upload_interval:
            bq_schema = gcloud.get_schema([sensor_data])
            if bq_schema:
                gcloud.update_bqtable(
                    schema=bq_schema,
                    table_data=[sensor_data],
                    project_id=project_id,
                    dataset_id=dataset_id,
                    table_id=table_id,
                )
                last_upload_time = datetime.now()

        time.sleep(sampling_interval)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
