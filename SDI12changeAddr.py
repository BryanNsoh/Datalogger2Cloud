#!/usr/local/opt/python-3.5.1/bin/python3.5
# SDI-12 Sensor Configuration Tool Copyright Dr. John Liu 2016-02-03
import serial.tools.list_ports
import serial
import time
import datetime
import re


def read_sensor_data(ser, sdi_12_address, measurement_code):
    """Reads data from a sensor connected to the serial port.

    Args:
        ser: The serial port object.
        sdi_12_address: The sensor address.
        measurement_code: The measurement code.

    Returns:
        A list of sensor values.
    """
    # Send the measurement command to the sensor.
    ser.write(sdi_12_address + b"C!")
    sdi_12_line = ser.readline()
    time.sleep(2.5)

    # Send the data command to the sensor.
    ser.write(sdi_12_address + b"D0!")
    # ser.write(sdi_12_address + b"D0!")

    # Read all of the lines from the serial port.
    lines = []
    try:
        while True:
            line = (
                ser.readline().decode().strip()
            )  # decode bytes to string and remove trailing newlines
            if not line:
                break
            lines.append(line)
    except Exception as e:
        print(f"Error reading from serial port: {e}")
        return None

    # Split the lines into a list of values
    sensor_values = [
        line[1:].split("+") for line in lines
    ]  # ignore the address, split at '+'

    # Return the list of cleaned sensor values
    return sensor_values


# Serial port detection
ports = list(serial.tools.list_ports.comports())
if len(ports) == 0:
    raise ValueError("No serial ports found")
elif len(ports) > 1:
    pass
serial_port = str(ports[0].device)

# Serial connection
ser = serial.Serial(serial_port, 9600, timeout=10)
time.sleep(2.5)

ser.write(b"?!")
sdi_12_line = ser.readline()

sdi_12_line = sdi_12_line[:-2]  # remove \r and \n since [0-9]$ has trouble with \r
m = re.search(b"[0-9a-zA-Z]$", sdi_12_line)  # having trouble with the \r
if m is None:
    print("No SDI-12 address found in the response: ", sdi_12_line.decode("utf-8"))
    exit(1)
else:
    sdi_12_address = m.group(0)  # find address


print("Sensor address:", sdi_12_address.decode("utf-8"))
ser.write(sdi_12_address + b"I!")
sdi_12_line = ser.readline()
print("Sensor info:", sdi_12_line.decode("utf-8"))

# user_sdi_12_address = input("\nEnter new address (0-9, A-Z, a-z)")
user_sdi_12_address = "1"

if (
    ((user_sdi_12_address >= "0") and (user_sdi_12_address <= "9"))
    or ((user_sdi_12_address >= "A") and (user_sdi_12_address <= "Z"))
    or ((user_sdi_12_address >= "a") and (user_sdi_12_address <= "z"))
):
    print("Sensor address changed to: ", user_sdi_12_address)
    ser.write(b"%sA%s!" % (sdi_12_address, user_sdi_12_address.encode("utf-8")))
    ser.readline()
    print("\nConfiguration complete.")

    # Query the sensor for data
    print("\nQuerying sensor for data...")
    measurement_code = b"MC!"
    sensor_data = read_sensor_data(
        ser, user_sdi_12_address.encode("utf-8"), measurement_code
    )
    print("Sensor_data: ")
    # print sensor_data array
    for value in sensor_data:
        print(value)

else:
    print("Address is invalid. No change was made.")
