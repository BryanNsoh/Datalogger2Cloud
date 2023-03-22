from pycampbellcr1000 import CR1000
import datetime
import traceback
import ndjson
import logger_query_functions as fxns
import gcloud_functions as gcloud
from serial import SerialException


""" Program using pycampbell library to collect and store data from datalogger 
    See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""


# Establish connection to datalogger
datalogger = CR1000.from_url("serial:/dev/ttyUSB0:38400")

# Get names of tables containing data
table_names = fxns.get_tables(datalogger)


while True:

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
