#!/usr/local/opt/python-3.5.1/bin/python3.5
# Simple SDI-12 Sensor Reader Copyright Dr. John Liu
import serial.tools.list_ports
import serial
import time
import re


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

ser.write(b"zM0!")
sdi_12_line = ser.readline()
sdi_12_line = ser.readline()
ser.write(b"zD0!")
sdi_12_line = ser.readline()
sdi_12_line = sdi_12_line[:-2]  # remove \r and \n
print("Sensor reading:", sdi_12_line.decode("utf-8"))
print(
    '\nFor complete data logging solution, download the free Python data logger under "data logger programs"\nhttps://liudr.wordpress.com/gadget/sdi-12-usb-adapter/'
)
ser.close()
