import serial.tools.list_ports
import serial
import time
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
import json
import threading
import logging
import pandas as pd
import numpy as np
from sqlite3 import Error
import platform, os
from database_functions import insert_data_to_db, setup_database
from gcloud_functions import get_schema, update_bqtable

# Configure logging
logging.basicConfig(
    filename="span2nodeA.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logging.getLogger("google").setLevel(logging.WARNING)

if platform.system() == "Linux":
    # Load the keys from the JSON file
    with open("/home/bryan/.keys/api_keys.json", "r") as file:
        keys = json.load(file)

    # Access keys for google service
    google_creds = keys["google"]["application_credentials"]

    # Set environment variable for Google credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds

elif platform.system() == "Windows":
    # Set environment variable for Google credentials
    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"
    ] = r"C:\.keys\crop2cloud-a9f1f94184a4.json"

else:
    raise OSError(
        "Unsupported operating system. This script runs on Linux and Windows only."
    )


# Create a lock for each sensor
lock1 = threading.Lock()

serial_id1 = "D30FETOH"


def get_sensor_profiles(file):
    with open(file, "r") as f:
        return json.load(f)


sensor_profiles1 = get_sensor_profiles("./span2nodeA_sensors.json")


def open_port_by_serial_number(serial_id):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if serial_id in port.hwid:
            return port.device
    raise ValueError(f"No serial port found for sensor {serial_id}")


serial_port1 = open_port_by_serial_number(serial_id1)

try:
    ser1 = serial.Serial(serial_port1, 9600, bytesize=8, stopbits=1, timeout=2.5)
    time.sleep(2.5)
except serial.SerialException as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    exit(1)


def read_sensor_data(ser, lock, sdi_12_address, measurement_code):
    with lock:
        ser.reset_input_buffer()
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

# Table name for Google Cloud and local database file
table_name = "span2nodeA"
local_db = "span2nodeA.db"


try:
    # Create an empty DataFrame with the columns you expect to have
    columns = ["TIMESTAMP"] + [
        "_" + sensor["sensor_id"] + suffix
        for sensor in sensor_profiles1
        if str(sensor.get("SDI-12 Address", "")).strip()
        and ("TDR" in sensor["sensor_id"] or "IRT" in sensor["sensor_id"])
        for suffix in (["_ST", "_VWC"] if "TDR" in sensor["sensor_id"] else [""])
    ]
    print(columns)

    # Create empty dataframe
    df = pd.DataFrame(columns=columns)

    # Loop to take readings
    for readings in range(1):
        # Initialize a dictionary for each reading iteration
        sensor_data = {"TIMESTAMP": datetime.now()}  # TIMESTAMP as datetime object

        # Sensors from sensor_profiles1
        for i, sensor in enumerate(sensor_profiles1):
            sdi_12_address_str = sensor.get("SDI-12 Address")
            # Proceed only if the sensor has a non-empty SDI-12 Address
            if (
                sdi_12_address_str
                and sdi_12_address_str.strip()
                and ("TDR" in sensor["sensor_id"] or "IRT" in sensor["sensor_id"])
            ):
                sdi_12_address = bytes(sdi_12_address_str.strip(), "utf-8")
                try:
                    sensor_values = read_sensor_data(ser1, lock1, sdi_12_address, b"M")
                    print(sensor_values)
                    if "TDR" in sensor["sensor_id"]:
                        sensor_data["_" + sensor["sensor_id"] + "_ST"] = (
                            float(sensor_values[1])
                            if len(sensor_values) >= 2
                            else np.nan
                        )
                        sensor_data["_" + sensor["sensor_id"] + "_VWC"] = (
                            float(sensor_values[0])
                            if len(sensor_values) >= 2
                            else np.nan
                        )
                    elif len(sensor_values) >= 1:
                        sensor_data["_" + sensor["sensor_id"]] = float(sensor_values[0])
                    else:
                        sensor_data["_" + sensor["sensor_id"]] = np.nan
                except Exception as e:
                    logging.error(
                        f"An error occurred when reading sensor {sensor['sensor_id']}: {e}",
                        exc_info=True,
                    )
                    sensor_data["_" + sensor["sensor_id"]] = np.nan
                print(sensor_data)

        # Append the sensor data from this iteration to the DataFrame using pd.concat
        df = pd.concat([df, pd.DataFrame([sensor_data])], ignore_index=True)

    print(df.dtypes)
    print(df)

    # Compute averages and append the timestamp
    averaged_df = df.mean(numeric_only=True).to_frame().T
    averaged_df.insert(0, "TIMESTAMP", datetime.now())

    # Save averaged_data_list to BigQuery table using gcloud_functions
    try:
        schema = get_schema(averaged_df.to_dict(orient="records"))
        update_bqtable(schema, table_name, averaged_df.to_dict(orient="records"))
    except Exception as e:
        logging.error(f"Failed to update BigQuery: {e}", exc_info=True)

    # Check if database exists, if not create it
    if not os.path.exists(local_db):
        schema = get_schema(averaged_df.to_dict(orient="records"))
        setup_database(schema, local_db)

    # Save averaged_data_list to sensor_data.db using database_functions
    try:
        insert_data_to_db(averaged_df.to_dict(orient="records"), local_db)
    except Exception as e:
        logging.error(f"Failed to update local SQLite database: {e}", exc_info=True)


except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
    ser1.close()
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    ser1.close()
