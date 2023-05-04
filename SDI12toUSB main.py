import serial.tools.list_ports
import serial
import time
from datetime import datetime, timedelta
import json
from typing import List, Dict
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
table_id = "SDI12Test"
bucket_name = "logger1-bucket"
blob_name = "plt-34/logger.json"


def read_sensor_data(ser, sdi_12_address, measurement_code):
    # Send the measurement command to the sensor
    ser.write(sdi_12_address + b"M" + measurement_code + b"!")
    # Read and discard the first line of the response
    sdi_12_line = ser.readline()
    # Read and discard the second line of the response
    sdi_12_line = ser.readline()
    # Send the data command to the sensor
    ser.write(sdi_12_address + b"D0!")
    # Read the third line of the response, which contains the data
    sdi_12_line = ser.readline()
    # Remove the newline characters from the end of the line
    sdi_12_line = sdi_12_line[:-2]
    # Split the response into a list of values, excluding the first element (sensor address)
    sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]

    # Iterate through the sensor values
    for i, value in enumerate(sensor_values):
        # If a negative sign is found in the value (indicating a diagnostic value)
        if "-" in value:
            # Split the value at the negative sign, keeping only the first part (soil moisture value)
            sensor_values[i] = value.split("-")[0]

    # Return the list of cleaned sensor values
    return sensor_values


# Initialize sensor data variables
sensor_0_temperature = None
sensor_1_soil_moisture = None
sensor_data_list = []
sampling_interval = 1  # 1 minute (60)
upload_interval = 3  # 1 hour(3600)
last_upload_time = datetime.now() - timedelta(seconds=upload_interval)

try:
    while True:
        current_time = datetime.now()

        # Read sensor data
        sensor_0_values = read_sensor_data(ser, b"0", b"1")
        if len(sensor_0_values) >= 2:
            sensor_0_temperature = float(sensor_0_values[1])

        sensor_1_values = read_sensor_data(ser, b"1", b"1")
        if len(sensor_1_values) >= 2:
            sensor_1_soil_moisture = float(sensor_1_values[1])

        # Store sensor data in a dictionary
        sensor_data = {
            "Datetime": current_time.isoformat(),
            "ApogeeT": sensor_0_temperature,
            "CS655_SoilMoisture": sensor_1_soil_moisture,
        }

        # Append sensor data to the list
        if sensor_0_temperature is not None and sensor_1_soil_moisture is not None:
            sensor_data_list.append(sensor_data)

        # Save sensor data to a file
        with open("./sensor_data.json", "a") as f:
            json.dump(sensor_data, f)
            f.write("\n")

        # Push sensor data to BigQuery and Google Cloud Storage every hour
        if (current_time - last_upload_time).total_seconds() >= upload_interval:
            bq_schema = gcloud.get_schema(sensor_data_list)
            if bq_schema:
                gcloud.update_bqtable(
                    schema=bq_schema,
                    table_data=sensor_data_list,
                    project_id=project_id,
                    dataset_id=dataset_id,
                    table_id=table_id,
                )
                gcloud.update_bucket(
                    bucket_name=bucket_name,
                    blob_name=blob_name,
                )
            last_upload_time = current_time
            sensor_data_list = []

        time.sleep(sampling_interval)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
