import serial.tools.list_ports
import serial
import time
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
import json
import threading
from typing import List, Dict
import logging
import pandas as pd
import pandas_gbq
import numpy as np
import sqlite3
from sqlite3 import Error

# Configure logging
logging.basicConfig(
    filename="SDI12toUSB.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logging.getLogger("google").setLevel(logging.WARNING)


# Create a lock for each sensor
lock1 = threading.Lock()

serial_id1 = "D30FEUP2"


def get_sensor_profiles(file):
    with open(file, "r") as f:
        return json.load(f)


sensor_profiles1 = get_sensor_profiles("span2nodeB.json")


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


def table_exists(
    client: bigquery.Client, table_ref: bigquery.table.TableReference
) -> bool:
    try:
        client.get_table(table_ref)
        return True
    except NotFound:
        return False


def update_bigquery(client, dataset_id, table_id, df):
    full_table_id = f"{client.project}.{dataset_id}.{table_id}"

    # Check if table exists
    table_ref = client.dataset(dataset_id).table(table_id)
    if_exists_value = "append" if table_exists(client, table_ref) else "replace"

    df.to_gbq(
        full_table_id,
        project_id=client.project,
        if_exists=if_exists_value,  # Append to the existing table or replace if it doesn't exist
        progress_bar=True,
    )
    print(f"Successfully updated table {full_table_id}")


def get_bq_table(table_name):
    # Get the table_id, project_id, and dataset_id for table_name
    table_params = {
        "span2nodeB": {
            "project_id": "crop2cloud",
            "dataset_id": "sensor_data",
            "table_id": "span2nodeB",
        },
        "span2nodeC": {
            "project_id": "crop2cloud",
            "dataset_id": "sensor_data",
            "table_id": "span2nodeC",
        },
        "span2nodeA": {
            "project_id": "crop2cloud",
            "dataset_id": "sensor_data",
            "table_id": "span2nodeA",
        },
        "span5_all": {
            "project_id": "crop2cloud",
            "dataset_id": "sensor_data",
            "table_id": "span5_all",
        },
        "weather": {
            "project_id": "crop2cloud",
            "dataset_id": "weather_data",
            "table_id": "weather",
        },
    }

    return [
        table_params[table_name]["project_id"],
        table_params[table_name]["dataset_id"],
        table_params[table_name]["table_id"],
    ]


def create_conn(db_file):
    """Create a database connection to a SQLite database"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"sqlite3 version: {sqlite3.version}")
    except Error as e:
        print(e)
    return conn


sensor_data_list = []

# Initialize a BigQuery client
client = bigquery.Client()


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
    for readings in range(3):
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

    # Save averaged_data_list to sensor_data.json (to be deprecated)
    averaged_df.to_json("sensor_data.json", orient="records", date_format="iso")

    # Save averaged_data_list to sensor_data.db using sqlite3
    conn = create_conn("sensor_data.db")
    averaged_df.to_sql("sensor_data", conn, if_exists="append", index=False)
    conn.close()

    # Save averaged_data_list to BigQuery table
    project_id, dataset_id, table_id = get_bq_table(
        "span2nodeB"
    )  # Use the right table name
    update_bigquery(client, dataset_id, table_id, averaged_df)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
    ser1.close()
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    ser1.close()
