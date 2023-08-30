import serial.tools.list_ports
import serial
import time
import json
import logging
import threading
import pandas as pd
from datetime import datetime
import gcloud_functions as gcloud

# Creating a lock for threading
lock = threading.Lock()


def create_serial_port(portname):
    return serial.Serial(portname, 9600, timeout=10)


def create_sensor(id: str, address: str, port, analog: bool = False):
    return {
        "id": id,
        "address": address,
        "analog": analog,
        "port": port,
        "df": pd.DataFrame(),
    }


def read(sensor):
    lock.acquire()  # Start of thread-safe section
    try:
        sensor["port"].reset_input_buffer()  # Flushing input buffer before reading
        if sensor["analog"]:
            data = read_analog(sensor)
        else:
            data = read_digital(sensor)
        sensor["port"].reset_output_buffer()  # Flushing output buffer after reading
        return data
    except Exception as e:
        logging.error(f"An error occurred while reading data: {e}", exc_info=True)
        return {}
    finally:
        lock.release()  # End of thread-safe section


def read_analog(sensor):
    try:
        sensor["port"].write(bytes(sensor["address"], "utf-8") + b"M8!")
        sdi_12_line = sensor["port"].readline()
        sdi_12_line = sensor["port"].readline()
        sensor["port"].write(bytes(sensor["address"], "utf-8") + b"D0!")
        sdi_12_line = sdi_12_line[:-2]
        sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]
        return {sensor["id"] + str(i): value for i, value in enumerate(sensor_values)}
    except Exception as e:
        logging.error(
            f"An error occurred while reading analog data: {e}", exc_info=True
        )
        return {}


def read_digital(sensor):
    try:
        sensor_values = read_sensor_data(sensor)

        if "IRT" in sensor["id"]:
            return {sensor["id"]: sensor_values[0]}
        elif "TDR" in sensor["id"] and len(sensor_values) > 2:
            return {
                sensor["id"] + "_VWC": sensor_values[0],
                sensor["id"] + "_ST": sensor_values[1],
            }
        else:
            return {sensor["id"]: value for value in sensor_values}
    except Exception as e:
        logging.error(
            f"An error occurred while reading digital data: {e}", exc_info=True
        )
        return {}


def read_sensor_data(sensor):
    sensor["port"].write(bytes(sensor["address"], "utf-8") + b"I" + b"!")
    sdi_12_line = sensor["port"].readline()
    print(sdi_12_line)
    sdi_12_line = sensor["port"].readline()
    print(sdi_12_line)
    sensor["port"].write(bytes(sensor["address"], "utf-8") + b"D0!")
    sdi_12_line = sensor["port"].readline()
    sdi_12_line = sdi_12_line[:-2]
    sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]

    for i, value in enumerate(sensor_values):
        if "-" in value:
            parts = value.split("-")
            parts[1] = "-" + parts[1]
            sensor_values[i] = parts

    return sensor_values


def open_port_by_serial_number(serial_number):
    for port in serial.tools.list_ports.comports():
        if port.serial_number == serial_number:
            return port.device
    raise Exception("No port found with specified serial number")


serial_numbers = ["D30EQ9PU", "D30FETNY"]
ports = [
    create_serial_port(open_port_by_serial_number(serial_number))
    for serial_number in serial_numbers
]

sensor_files = ["./sensor_profiles1.json", "./sensor_profiles2.json"]
sensors = []
for i, sensor_file in enumerate(sensor_files):
    with open(sensor_file) as f:
        sensor_profiles = json.load(f)
    for profile in sensor_profiles:
        sensor_id = profile["sensor_id"]
        address = profile["SDI-12 Address"]
        analog = bool(profile["Analog address"])
        sensors.append(create_sensor(sensor_id, address, ports[i], analog))


def read_all_sensors():
    sensor_data = []
    for sensor in sensors:
        sensor_data.append(read(sensor))
    df = pd.DataFrame(sensor_data)
    return df


# Configure logging
logging.basicConfig(
    filename="SDI12toUSB.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logging.getLogger("google").setLevel(logging.WARNING)

# BigQuery and Google Cloud Storage configurations
project_id = "apt-rite-378417"
dataset_id = "loggertest1"
table_id = "SDI12Test2"

df = pd.DataFrame()

try:
    sensor_data = read_all_sensors()
    sensor_data["Datetime"] = datetime.now().isoformat()
    df = df.append(sensor_data)

    # Push sensor data to BigQuery and Google Cloud Storage
    bq_schema = gcloud.get_schema([df.to_dict(orient="records")])
    if bq_schema:
        gcloud.update_bqtable(
            schema=bq_schema,
            table_data=df.to_dict(orient="records"),
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
        )
    df = pd.DataFrame()

    # Save sensor data to a file
    with open("./sensor_data.json", "a") as f:
        json.dump(df.to_dict(orient="records"), f)
        f.write("\n")

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
