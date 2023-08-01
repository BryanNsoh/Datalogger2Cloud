import serial.tools.list_ports
import serial
import time
from datetime import datetime, timedelta
import json
import threading
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
lock2 = threading.Lock()


def get_sensor_profiles(file):
    with open(file, "r") as f:
        return json.load(f)


sensor_profiles1 = get_sensor_profiles("sensor_profiles1.json")
sensor_profiles2 = get_sensor_profiles("sensor_profiles2.json")

serial_id1 = "D30FETO3"
serial_id2 = "D30FETNY"


def open_port_by_serial_number(serial_id):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if serial_id in port.hwid:
            return port.device
    raise ValueError(f"No serial port found for sensor {serial_id}")


serial_port1 = open_port_by_serial_number(serial_id1)
serial_port2 = open_port_by_serial_number(serial_id2)

try:
    ser1 = serial.Serial(serial_port1, 9600, bytesize=8, stopbits=1, timeout=5)
    ser2 = serial.Serial(serial_port2, 9600, bytesize=8, stopbits=1, timeout=5)
    time.sleep(2.5)
except serial.SerialException as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    exit(1)


def parse_response_time(ack):
    # Remove end line characters
    ack = ack.strip()
    # Get the delay time (ttt) which is the 3 characters after the 'a'
    delay_time = ack.decode("utf-8")[1:4]
    return float(delay_time)


def read_sensor_data(ser, lock, sdi_12_address, measurement_code):
    with lock:
        # Flush buffers
        ser.reset_input_buffer()

        if ser.isOpen():
            print("Serial port is open")
        else:
            print("Serial port is not open")

        # Send the measurement command to the sensor
        ser.write(sdi_12_address + measurement_code)
        # Read the acknowledgement from the sensor
        # Read and discard the first line of the response
        sdi_12_line = ser.readline()
        # Read and discard the second line of the response
        sdi_12_line = ser.readline()
        # Send the data command to the sensor
        ser.write(sdi_12_address + b"D0!")
        # Read the third line of the response, which contains the data
        sdi_12_line = ser.readline()
        # Flush buffers
        ser.reset_output_buffer()

    sdi_12_line = sdi_12_line[:-2]
    sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]

    for i, value in enumerate(sensor_values):
        if "-" in value:
            parts = value.split("-")
            parts[1] = "-" + parts[1]
            sensor_values[i] = parts

    return sensor_values


sampling_interval = 6  # 1 minute (60)
upload_interval = 36  # 1 hour(3600)
last_upload_time = datetime.now() - timedelta(seconds=upload_interval)

try:
    while True:
        current_time = datetime.now()
        sensor_data = {"Datetime": current_time.isoformat()}

        for sensor_profile, ser, lock in zip(
            [sensor_profiles1, sensor_profiles2], [ser1, ser2], [lock1, lock2]
        ):
            for sensor in sensor_profile:
                sdi_12_address = bytes(sensor["SDI-12 Address"], "utf-8")
                sensor_values = read_sensor_data(ser, lock, sdi_12_address, b"M!")
                if len(sensor_values) >= 2:
                    sensor_data[sensor["sensor_id"]] = float(sensor_values[1])

        print(sensor_data)

        with open("./sensor_data.json", "a") as f:
            json.dump(sensor_data, f)
            f.write("\n")

        time.sleep(sampling_interval)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
    ser1.close()
    ser2.close()
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
    ser1.close()
    ser2.close()
