import os
import pandas as pd
from datetime import datetime, timedelta
import threading
from SDI12toUSB_main import Sensor, sensor_profiles
from pycampbellcr1000 import CR1000
import ndjson
import logger_query_functions as lqf
import gcloud_functions as gcloud
import logging

logging.basicConfig(
    filename="main_query.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)

logging.getLogger("google").setLevel(logging.WARNING)


def collect_data():
    # Initialize sensors
    sensors = [Sensor(id, **params) for id, params in sensor_profiles.items()]
    # Create a dataframe to hold sensor data
    sensor_df = pd.DataFrame()

    # Start the collection loop
    while True:
        # Collect data every 15 minutes
        threading.Timer(900, collect_data).start()
        sensor_data = {}
        for sensor in sensors:
            try:
                sensor_data.update(sensor.read())
            except Exception as e:
                logging.error(
                    f"An error occurred during sensor reading: {e}", exc_info=True
                )
        # Append sensor data to dataframe
        sensor_df = sensor_df.append(sensor_data, ignore_index=True)


def process_data():
    # Establish connection to datalogger
    datalogger = CR1000.from_url("serial:/dev/ttyUSB0:38400")

    while True:
        # Process data every hour
        threading.Timer(3600, process_data).start()

        # Get names of tables containing data
        table_names = lqf.get_tables(datalogger)

        # Get data collection interval
        start, stop = lqf.track_and_manage_time(datalogger)

        try:
            # Get table data and convert to DataFrame
            table_data_listdict = lqf.get_data(
                datalogger, table_names[1].decode("utf-8"), start, stop
            )
            table_data = pd.DataFrame(table_data_listdict)

            # Merge table_data and sensor_data
            combined_df = pd.concat([sensor_df, table_data], axis=1)

            # Calculate rolling average over 1 hour (4*15 minutes)
            averaged_df = combined_df.rolling(window=4).mean()

            # Update BigQuery table with averaged data
            project_id = "apt-rite-378417"
            dataset_id = "final_test"
            table_id = "corn_test"
            schema = gcloud.get_schema(table_data)
            gcloud.update_bqtable(schema, averaged_df, project_id, dataset_id, table_id)

            logging.info("Upload success!")
        except Exception as e:
            logging.error(f"An error occurred during processing: {e}", exc_info=True)

        # Clear sensor_df for the next hour
        sensor_df = pd.DataFrame()


if __name__ == "__main__":
    collect_data()
    process_data()
