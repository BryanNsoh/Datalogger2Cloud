"""
Simple SDI-12 Sensor Reader
Adapted from code by Dr. John Liu
"""

import serial.tools.list_ports
import serial
import time
from datetime import datetime
import json
from typing import List, Dict
import gcloud_functions as gcloud

# Detect available serial ports
port_names = []
a = serial.tools.list_ports.comports()

user_port_selection = input(
    "\nSelect port from list (0,1,2...). SDI-12 adapter has USB VID=0403:"
)
port_device = a[int(user_port_selection)].device

ser = serial.Serial(port=port_device, baudrate=9600, timeout=10)
time.sleep(2.5)

sensor_data = {}


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

# BigQuery and Google Cloud Storage configurations
project_id = "apt-rite-378417"
dataset_id = "loggertest1"
table_id = "DRLiuTest"
bucket_name = "logger1-bucket"
blob_name = "plt-34/logger.json"

sensor_data_list = []

while True:
    try:
        # Read sensor data
        sensor_0_values = read_sensor_data(ser, b"0", b"1")
        if len(sensor_0_values) >= 2:
            sensor_0_temperature = float(sensor_0_values[1])

        sensor_1_values = read_sensor_data(ser, b"1", b"1")
        if len(sensor_1_values) >= 2:
            sensor_1_soil_moisture = float(sensor_1_values[0])

        # Print sensor data
        if sensor_0_temperature is not None:
            print("Apogee temperature: {:.4f} °C".format(sensor_0_temperature))

        if sensor_1_soil_moisture is not None:
            print("CS655 soil moisture: {:.4f} cm^3/cm".format(sensor_1_soil_moisture))

        # Store sensor data in a dictionary
        sensor_data = {
            "Datetime": datetime.utcnow().isoformat(),
            "ApogeeT": sensor_0_temperature,
            "CS655_SoilMoisture": sensor_1_soil_moisture,
        }

        # Append sensor data to the list
        sensor_data_list.append(sensor_data)

        # Save sensor data to a file
        with open("./sensor_data.json", "a") as f:
            json.dump(sensor_data, f)
            f.write("\n")

        # Push sensor data to BigQuery and Google Cloud Storage
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

        time.sleep(1)

    except KeyboardInterrupt:
        print("Interrupted by user. Exiting...")
        break
    except Exception as e:
        print(f"Error: {str(e)}")
