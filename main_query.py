from pycampbellcr1000 import CR1000
import os
import ndjson
import logger_query_functions as lqf
import gcloud_functions as gcloud
import logging

logging.basicConfig(filename="main_query_error.log", level=logging.ERROR)

""" Program using pycampbell library to collect and store data from a CR800 or CR1000 datalogger
    See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""

try:
    # Establish connection to datalogger
    datalogger = CR1000.from_url("serial:/dev/ttyUSB0:38400")

    # Get names of tables containing data
    table_names = lqf.get_tables(datalogger)

    # Get data collection interval
    start, stop = lqf.track_and_manage_time(datalogger)

    # Get table data
    table_data = lqf.get_data(datalogger, table_names[1].decode("utf-8"), start, stop)

    # Storing the data to a local ndjson file
    lqf.store_in_ndjson(table_data)

    # send stored data to GCloud
    # Gcloud.update_bucket()
    schema = gcloud.get_schema(table_data)
    update_table = gcloud.update_bqtable(schema, table_data)

except Exception as e:
    logging.error(f"An error occurred: {e}")
