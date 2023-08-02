import serial.tools.list_ports
import serial
import time
from datetime import datetime, timedelta
import json
import threading
from typing import List, Dict
import gcloud_functions as gcloud
import logging
import pandas as pd

# Configure logging
logging.basicConfig(
    filename="SDI12toUSB.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logging.getLogger("google").setLevel(logging.WARNING)

# Create a lock for each sensor
lock1 = threading.Lock()

serial_id1 = "D30FETNY"


def get_sensor_profiles(file):
    with open(file, "r") as f:
        return json.load(f)


sensor_profiles1 = get_sensor_profiles("span5_all.json")


def open_port_by_serial_number(serial_id):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if serial_id in port.hwid:
            return port.device
    raise ValueError(f"No serial port found for sensor {serial_id}")


serial_port1 = open_port_by_serial_number(serial_id1)

try:
    ser1 = serial.Serial(serial_port1, 9600, bytesize=8, stopbits=1, timeout=5)
    time.sleep(2.5)
except serial.SerialException as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    exit(1)


def read_sensor_data(ser, lock, sdi_12_address, measurement_code):
    with lock:
        ser.reset_input_buffer()
        if ser.isOpen():
            print("Serial port is open")
        else:
            print("Serial port is not open")
        ser.write(sdi_12_address + measurement_code + b"!")
        print(f"Sent command {sdi_12_address + measurement_code + b'!'}")
        sdi_12_line = ser.readline()
        sdi_12_line = ser.readline()
        ser.write(sdi_12_address + b"D0!")
        sdi_12_line = ser.readline()
        ser.reset_output_buffer()

    sdi_12_line = sdi_12_line[:-2]
    sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]

    for i, value in enumerate(sensor_values):
        if "-" in value:
            parts = value.split("-")
            parts[1] = "-" + parts[1]
            sensor_values[i] = parts

    return sensor_values


sensor_data_list = []


try:
    # Create an empty DataFrame to store sensor data readings
    df = pd.DataFrame()

    # Loop to take readings thrice
    for readings in range(3):
        # Initialize an empty dictionary for each reading iteration
        sensor_data = {"TIMESTAMP": datetime.now().isoformat()}

        # Sensors from sensor_profiles1
        for i, sensor in enumerate(sensor_profiles1):
            sdi_12_address_str = sensor.get("SDI-12 Address")
            print(sensor["sensor_id"])
            # Proceed only if the sensor has a non-empty SDI-12 Address
            if sdi_12_address_str and sdi_12_address_str.strip():
                sdi_12_address = bytes(sdi_12_address_str.strip(), "utf-8")
                try:
                    sensor_values = read_sensor_data(ser1, lock1, sdi_12_address, b"M1")
                    if len(sensor_values) >= 2:
                        sensor_data[sensor["sensor_id"]] = float(sensor_values[1])
                    else:
                        sensor_data[sensor["sensor_id"]] = -9999
                except Exception as e:
                    logging.error(
                        f"An error occurred when reading sensor {sensor['sensor_id']}: {e}",
                        exc_info=True,
                    )
                    sensor_data[sensor["sensor_id"]] = -9999
                print(sensor_data)

        # Append the sensor data from this iteration to the DataFrame
        df = df.append(sensor_data, ignore_index=True)

    # Replace -9999 with NaN for averaging
    df.replace(-9999, pd.NA, inplace=True)

    # Compute averages
    averaged_data = df.mean(numeric_only=True).to_dict()

    # Replace NaN values with -9999 for compatibility with BigQuery
    for key, value in averaged_data.items():
        if pd.isna(value):
            averaged_data[key] = -9999

    # Update TIMESTAMP with current timestamp
    averaged_data["TIMESTAMP"] = datetime.now().isoformat()

    # Convert the averaged_data to list of dict
    averaged_data_list = [averaged_data]

    # Save averaged_data_list to sensor_data.json
    with open("sensor_data.json", "w") as file:
        json.dump(averaged_data_list, file)

    # Update bigquery
    schema = gcloud.get_schema(averaged_data)
    gcloud.update_bqtable(
        schema=schema, table_name="span5_all", table_data=averaged_data
    )


except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
    ser1.close()
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    ser1.close()
