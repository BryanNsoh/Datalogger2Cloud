import sensors
from datetime import datetime, timedelta
import time
import json
import gcloud_functions as gcloud
import logging

# Configure logging
logging.basicConfig(
    filename="SDI12toUSB.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logging.getLogger("google").setLevel(logging.WARNING)

# BigQuery and Google Cloud Storage configurations
project_id = "apt-rite-378417"
dataset_id = "loggertest1"
table_id = "SDI12Test2"

last_upload_time = datetime.now()
upload_interval = 60  # In seconds, update according to your requirement
sampling_interval = 1  # In seconds, update according to your requirement

try:
    while True:
        sensor_data = {"Datetime": datetime.now().isoformat()}
        for sensor in sensors.sensors:
            sensor_data.update(sensor.read(sensors.ser))

        # Push sensor data to BigQuery and Google Cloud Storage
        if (datetime.now() - last_upload_time).total_seconds() >= upload_interval:
            bq_schema = gcloud.get_schema([sensor_data])
            if bq_schema:
                gcloud.update_bqtable(
                    schema=bq_schema,
                    table_data=[sensor_data],
                    project_id=project_id,
                    dataset_id=dataset_id,
                    table_id=table_id,
                )
                last_upload_time = datetime.now()

        # Save sensor data to a file
        with open("./sensor_data.json", "a") as f:
            json.dump(sensor_data, f)
            f.write("\n")

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
