#!/usr/local/opt/python-3.5.1/bin/python3.5
# Simple SDI-12 Sensor Reader Copyright Dr. John Liu
import serial.tools.list_ports
import serial
import time
import re

serial_id1 = "D30EQ9PU"


def open_port_by_serial_number(serial_id):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if serial_id in port.hwid:
            return port.device
    raise ValueError(f"No serial port found for sensor {serial_id}")


serial_port1 = open_port_by_serial_number(serial_id1)

try:
    ser = serial.Serial(serial_port1, 9600, bytesize=8, stopbits=1, timeout=5)
    time.sleep(2.5)
except serial.SerialException as e:
    exit(1)

ser.write(b"?!")
sdi_12_line = ser.readline()
sdi_12_line = sdi_12_line[:-2]  # remove \r and \n since [0-9]$ has trouble with \r
m = re.search(b"[0-9a-zA-Z]$", sdi_12_line)  # having trouble with the \r
sdi_12_address = m.group(0)  # find address
print("\nSensor address:", sdi_12_address.decode("utf-8"))

ser.write(sdi_12_address + b"I!")
sdi_12_line = ser.readline()
sdi_12_line = sdi_12_line[:-2]  # remove \r and \n
print("Sensor info:", sdi_12_line.decode("utf-8"))

ser.write(sdi_12_address + b"M4!")
sdi_12_line = ser.readline()
sdi_12_line = ser.readline()
ser.write(sdi_12_address + b"D0!")
sdi_12_line = ser.readline()
sdi_12_line = sdi_12_line[:-2]  # remove \r and \n
print("Sensor reading:", sdi_12_line.decode("utf-8"))
print(
    '\nFor complete data logging solution, download the free Python data logger under "data logger programs"\nhttps://liudr.wordpress.com/gadget/sdi-12-usb-adapter/'
)
ser.close()
