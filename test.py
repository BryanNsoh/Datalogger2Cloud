import serial.tools.list_ports
import serial
import time
from datetime import datetime, timedelta
import json
import threading
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
    while True:
        current_time = datetime.now()
        sensor_data = {
            "Datetime": current_time.isoformat(),
        }

        # Sensors from sensor_profiles1
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

        print(sensor_data)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
    ser1.close()
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    ser1.close()
