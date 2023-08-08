from pycampbellcr1000 import CR1000
import os
import ndjson
import logger_query_functions as lqf
import gcloud_functions as gcloud
import logging
import datetime

# Importing SQLite3 database functions
from database_functions import setup_database, insert_data_to_db, get_latest_timestamp


# Configure logging
logging.basicConfig(
    filename="main_query.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)

logging.getLogger("google").setLevel(logging.WARNING)

"""Program using pycampbell library to collect and store data from a CR800 or CR1000 datalogger.
   See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""
# Table name for Google Cloud
table_name = "span2nodeB"
local_db_name = "span2nodeB.db"


def main():
    try:
        # Establish connection to datalogger
        datalogger = CR1000.from_url("serial:/dev/ttyUSB0:38400")

        # Get names of tables containing data
        table_names = lqf.get_tables(datalogger)

        # Check SQLite3 for latest entry time
        latest_time = get_latest_timestamp(local_db_name)

        # Determine start and stop times
        if latest_time:
            start = datetime.datetime.fromisoformat(latest_time)
            stop = start + datetime.timedelta(minutes=30)
        else:
            current_year = datetime.datetime.now().year
            start = datetime.datetime(current_year, 7, 23)
            stop = start + datetime.timedelta(minutes=30)

        # Get table data
        table_data = lqf.get_data(
            datalogger, table_names[1].decode("utf-8"), start, stop
        )

        # Send stored data to GCloud
        schema = gcloud.get_schema(table_data)

        # Update BigQuery table
        gcloud.update_bqtable(schema, table_name, table_data)

        # Check if database exists, if not create it
        if not os.path.exists("span2nodeB.db"):
            setup_database(schema, local_db_name)

        # Store the data in SQLite3 database
        insert_data_to_db(table_data, local_db_name)

        # Report Success
        logging.info("Upload success!")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
