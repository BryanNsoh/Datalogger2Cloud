import sensors
from datetime import datetime
import json
import gcloud_functions as gcloud
import logging
import pandas as pd

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

df = pd.DataFrame()

try:
    sensor_data = sensors.read_all_sensors()
    sensor_data["Datetime"] = datetime.now().isoformat()
    df = df.append(sensor_data)

    # Push sensor data to BigQuery and Google Cloud Storage
    bq_schema = gcloud.get_schema([df.to_dict(orient="records")])
    if bq_schema:
        gcloud.update_bqtable(
            schema=bq_schema,
            table_data=df.to_dict(orient="records"),
            project_id=project_id,
            dataset_id=dataset_id,
            table_id=table_id,
        )
    df = pd.DataFrame()

    # Save sensor data to a file
    with open("./sensor_data.json", "a") as f:
        json.dump(df.to_dict(orient="records"), f)
        f.write("\n")

except KeyboardInterrupt:
    logging.info("Interrupted by user. Exiting...")
except Exception as e:
    logging.error(f"An error occurred: {e}", exc_info=True)
