#!/usr/local/opt/python-3.5.1/bin/python3.5
import serial.tools.list_ports
import serial
import time
import re
import json


# Function to read sensor data
def read_sensor_data(ser, sdi_12_address):
    ser.write(sdi_12_address + b"I!")
    sdi_12_line = ser.readline()
    sdi_12_line = sdi_12_line[:-2]
    sensor_info = sdi_12_line.decode("utf-8")

    ser.write(sdi_12_address + b"M!")
    sdi_12_line = ser.readline()
    sdi_12_line = ser.readline()
    ser.write(sdi_12_address + b"D0!")
    sdi_12_line = ser.readline()
    sdi_12_line = sdi_12_line[:-2]
    sensor_reading = sdi_12_line.decode("utf-8")

    return sensor_info, sensor_reading


rev_date = "2018-12-03"
version = "1.0"

print("+-" * 40)
print("Simple SDI-12 Sensor Reader", version)
print(
    "Designed for Dr. Liu's family of SDI-12 USB adapters (standard,analog,GPS)\n\tDr. John Liu Saint Cloud MN USA",
    rev_date,
    "\n\t\tFree software GNU GPL V3.0",
)
print(
    "\nCompatible with PCs running Win 7/10, GNU/Linux, Mac OSX, Raspberry PI, Beagle Bone Black"
)
print("\nThis program requires Python 3.4, Pyserial 3.0")
print("\nFor assistance with customization, telemetry etc., contact Dr. Liu.")
print("\nhttps://liudr.wordpress.com/gadget/sdi-12-usb-adapter/")
print("+-" * 40)

port_names = []
a = serial.tools.list_ports.comports()
print("\nDetected the following serial ports:")
i = 0
for w in a:
    vidn = w.vid if (type(w.vid) is int) else 0
    print("%d)\t%s\t(USB VID=%04X)" % (i, w.device, vidn))
    i = i + 1
user_port_selection = input(
    "\nSelect port from list (0,1,2...). SDI-12 adapter has USB VID=0403:"
)
# Store the device name to open port with later in the script.
port_device = a[int(user_port_selection)].device

ser = serial.Serial(port=port_device, baudrate=9600, timeout=10)
time.sleep(2.5)  # delay for arduino bootloader and the 1 second delay of the adapter.

# Initialize sensor data dictionary
sensor_data = {}

# Read data from two sensors with addresses 0 and 1
for address in [b"0", b"1"]:
    sensor_info, sensor_reading = read_sensor_data(ser, address)
    sensor_data[address.decode("utf-8")] = {
        "info": sensor_info,
        "reading": sensor_reading,
    }
    print("Sensor {} info: {}".format(address.decode("utf-8"), sensor_info))
    print("Sensor {} reading: {}".format(address.decode("utf-8"), sensor_reading))

# Save sensor data to a JSON file
with open("sensor_data.json", "w") as f:
    json.dump(sensor_data, f, indent=4)
