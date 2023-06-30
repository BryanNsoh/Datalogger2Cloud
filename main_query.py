from pycampbellcr1000 import CR1000
import os
import ndjson
import logger_query_functions as lqf
import gcloud_functions as gcloud
import logging
import datetime

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


def main():
    try:
        # Establish connection to datalogger
        datalogger = CR1000.from_url("serial:/dev/ttyUSB0:38400")

        # Get names of tables containing data
        table_names = lqf.get_tables(datalogger)

        # Get data collection interval
        start, stop = lqf.track_and_manage_time(datalogger)

        # Get table data
        table_data = lqf.get_data(
            datalogger, table_names[1].decode("utf-8"), start, stop
        )

        # Send stored data to GCloud
        schema = gcloud.get_schema(table_data)

        # IDs and paths for Google Cloud
        project_id = "fourth-castle-388922"
        dataset_id = "final_test"
        table_id = "dry_test"

        # Update BigQuery table
        gcloud.update_bqtable(schema, table_data, project_id, dataset_id, table_id)

        # Storing the data to a local ndjson file
        lqf.store_in_ndjson(table_data)

        # Report Success
        logging.info("Upload success!")

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
