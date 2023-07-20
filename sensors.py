import serial.tools.list_ports
import serial
import time
import json
import logging
import pandas as pd


class SerialPort:
    def __init__(self, portname):
        self.ser = serial.Serial(portname, 9600, timeout=10)
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
        try:
            self.port.write(bytes(self.address, "utf-8") + b"M8!")
            sdi_12_line = self.port.readline()
            sdi_12_line = self.port.readline()
            self.port.write(bytes(self.address, "utf-8") + b"D0!")
            sdi_12_line = sdi_12_line[:-2]
            sensor_values = sdi_12_line.decode("utf-8").split("+")[1:]
            return {self.id + str(i): value for i, value in enumerate(sensor_values)}
        except Exception as e:
            logging.error(
                f"An error occurred while reading analog data: {e}", exc_info=True
            )
            return {}

    def read_digital(self):
        try:
            sensor_values = self.read_sensor_data(
                self.port, bytes(self.address, "utf-8"), b"I"
            )

            if "IRT" in self.id:
                return {self.id: sensor_values[0]}
            elif "TDR" in self.id and len(sensor_values) > 2:
                return {
                    self.id + "_VWC": sensor_values[0],
                    self.id + "_ST": sensor_values[1],
                }
            else:
                return {self.id: value for value in sensor_values}
        except Exception as e:
            logging.error(
                f"An error occurred while reading digital data: {e}", exc_info=True
            )
            return {}

    def read_sensor_data(self, ser, sdi_12_address, measurement_code):
        ser.write(sdi_12_address + measurement_code + b"!")
        sdi_12_line = ser.readline()
        print(sdi_12_line)
        sdi_12_line = ser.readline()
        print(sdi_12_line)
        ser.write(sdi_12_address + b"D0!")
        sdi_12_line = ser.readline()
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
        sensor_data.append(sensor.read())
    df = pd.DataFrame(sensor_data)
    return df
