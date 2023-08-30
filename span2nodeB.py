import serial.tools.list_ports
import serial
from pycampbellcr1000 import CR1000
import os
import logger_query_functions as lqf
import gcloud_functions as gcloud
import logging
import datetime

# Importing SQLite3 database functions
from database_functions import setup_database, insert_data_to_db, get_latest_timestamp

# Configure logging
logging.basicConfig(
    filename="span2nodeB.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)

logging.getLogger("google").setLevel(logging.WARNING)

"""Program using pycampbell library to collect and store data from a CR800 or CR1000 datalogger.
   See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""


def open_port_by_serial_number(serial_id):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if serial_id in port.hwid:
            return port.device


# Table name for Google Cloud and local database file
table_name = "span2nodeB"
local_db_name = "span2nodeB.db"

# Datalogger serial ID
serial_id = "AC025A1C"


def main():
    try:
        # Update system time
        try:
            gcloud.update_system_time()
        except:
            pass

        # Establish connection to datalogger
        datalogger = CR1000.from_url(
            f"serial:{open_port_by_serial_number(serial_id)}:38400"
        )

        # Get names of tables containing data
        table_names = lqf.get_tables(datalogger)

        # Check SQLite3 for latest entry time
        latest_time = get_latest_timestamp(local_db_name)

        # Determine start and stop times
        if latest_time:
            start = datetime.datetime.fromisoformat(latest_time)
            stop = datetime.datetime.now()
        else:
            current_year = datetime.datetime.now().year
            start = datetime.datetime(current_year, 7, 23)
            stop = datetime.datetime.now()

        # Get table data
        table_data = lqf.get_data(
            datalogger, table_names[1].decode("utf-8"), start, stop
        )

        # Send stored data to GCloud
        schema = gcloud.get_schema(table_data)

        # Try to update BigQuery table, if it fails, log the error but continue
        try:
            gcloud.update_bqtable(schema, table_name, table_data)
            logging.info("BigQuery upload success!")
        except Exception as bq_e:
            logging.error(
                f"An error occurred during BigQuery upload: {bq_e}", exc_info=True
            )

        # Attempt to store data in SQLite3 database
        try:
            # Check if database exists, if not create it
            if not os.path.exists("span2nodeB.db"):
                setup_database(schema, local_db_name)

            # Store the data
            insert_data_to_db(table_data, local_db_name)
            logging.info("SQLite database upload success!")
        except Exception as sqlite_e:
            logging.error(
                f"An error occurred during SQLite database upload: {sqlite_e}",
                exc_info=True,
            )

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
