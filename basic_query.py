from pycampbellcr1000 import CR1000
import datetime
import traceback
import ndjson
import logger_query_functions as fxns
import gcloud_functions as gcloud
from serial import SerialException
from pypakbus import PakBusClient, PakBusError

""" Program using pycampbell library to collect and store data from datalogger 
    See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""


# Configure the necessary parameters
device = "/dev/ttyUSB0"
local_ip = "192.168.27.236"
remote_ip = "10.0.0.1"

client = PakBusClient(
    host="192.168.0.100",  # Replace with the device's IP address if using Ethernet
    port=6785,  # Replace with the device's port number if using Ethernet
    serial_port="/dev/ttyUSB0",  # Replace with the appropriate serial port if using a serial connection
    baudrate=9600,  # Replace with the appropriate baud rate if using a serial connection
    station_id=1,
    timeout=5,
)

try:
    client.connect()
    print("Connected to the device")

    # Read data from the device here
    # ...

except PakBusError as e:
    print(f"PakBus error: {e}")

finally:
    client.disconnect()
    print("Disconnected from the device")


while True:

    # Get names of tables containing data
    table_names = fxns.get_tables(datalogger)

    # Get data collection interval
    start, stop = fxns.track_and_manage_time()

    # Ge data to be stored
    table_data = fxns.get_data(datalogger, table_names[1].decode("utf-8"), start, stop)

    local_file = "./CR800data.json"

    # Changing the default json class to

    try:
        with open(local_file, "w") as f:
            ndjson.dump(table_data, f)
    except FileNotFoundError:
        with open(local_file, "x") as f:
            ndjson.dump(table_data, f)

    # send stored data to GCloud
    # Gcloud.update_bucket()
    schema = gcloud.get_schema(table_data)
    gcloud.update_bqtable(schema, table_data)
