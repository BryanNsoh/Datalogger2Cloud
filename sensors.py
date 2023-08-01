import serial.tools.list_ports
import serial
import time
import json
import logging
import pandas as pd
import threading

# Constants for communication protocol
READ_ANALOG = b"M8!"
READ_DIGITAL = b"M!"
GET_DATA = b"D0!"
COMMAND_I = b"I!"

lock = threading.Lock()


class SerialPort:
    def __init__(
        self,
        portname,
        baud_rate=9600,
        timeout=10,
        bytesize=serial.EIGHTBITS,
        stopbits=serial.STOPBITS_ONE,
    ):
        self.ser = serial.Serial(
            portname, baud_rate, timeout=timeout, bytesize=bytesize, stopbits=stopbits
        )
        time.sleep(2.5)


class Sensor:
    def __init__(self, id: str, address: str, port: SerialPort, analog: bool = False):
        self.id = id
        self.address = address
        self.analog = analog
        self.port = port.ser
        self.df = pd.DataFrame()

    def read(self):
        if self.analog:
            return self.read_analog()
        else:
            return self.read_digital()

    def read_analog(self):
        return self.read_sensor_data(READ_ANALOG)

    def read_digital(self):
        try:
            sensor_values = self.read_sensor_data(
                bytes(self.address, "utf-8") + READ_DIGITAL
            )

            if sensor_values:  # Check if sensor_values is not empty
                if "IRT" in self.id:
                    return {self.id: sensor_values[0]}
                elif "TDR" in self.id and len(sensor_values) > 2:
                    return {
                        self.id + "_VWC": sensor_values[0],
                        self.id + "_ST": sensor_values[1],
                    }
                else:
                    return {self.id: value for value in sensor_values}
            else:
                logging.warning(f"No data received from the sensor {self.id}")
                return {}

        except Exception as e:
            logging.error(
                f"An error occurred while reading digital data: {e}", exc_info=True
            )
            return {}

    def read_sensor_data(self, measurement_code):
        try:
            with lock:
                self.port.reset_input_buffer()
                self.port.write(bytes(self.address, "utf-8") + measurement_code)
                sdi_12_line = self.port.readline()
                sdi_12_line = self.port.readline()
                self.port.write(bytes(self.address, "utf-8") + GET_DATA)
                sdi_12_line = sdi_12_line[:-2]
                self.port.reset_output_buffer()

            sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]
            for i, value in enumerate(sensor_values):
                if "-" in value:
                    if "-" in value:
                        parts = value.split("-")
                        parts[1] = "-" + parts[1]
                        sensor_values[i] = "".join(parts)

            return sensor_values
        except serial.SerialException as e:
            logging.error(f"An error occurred while reading data: {e}", exc_info=True)
            raise


def open_port_by_serial_number(serial_number):
    for port in serial.tools.list_ports.comports():
        if port.serial_number == serial_number:
            return port.device
    raise Exception("No port found with specified serial number")


serial_numbers = ["D30FETO3", "D30FETNY"]
ports = [
    SerialPort(open_port_by_serial_number(serial_number))
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
        sensors.append(Sensor(sensor_id, address, ports[i], analog))


def read_all_sensors():
    sensor_data = []
    for sensor in sensors:
        try:
            sensor_data.append(sensor.read())
        except serial.SerialException as e:
            logging.error(
                f"An error occurred while reading data from sensor {sensor.id}: {e}",
                exc_info=True,
            )
    df = pd.DataFrame(sensor_data)
    return df


if __name__ == "__main__":
    try:
        data = read_all_sensors()
        print(data)
    finally:
        for port in ports:
            port.ser.close()
