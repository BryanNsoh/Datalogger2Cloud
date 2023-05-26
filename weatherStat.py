import json
import time
import logging
import logging.handlers
import os
from ambient_api.ambientapi import AmbientAPI

import gcloud_functions as gcloud

# Google Cloud details
project_id = "apt-rite-378417"
dataset_id = "loggertest1"
table_id = "RBpiTest"
local_file = "./CR800data.json"
bucket_name = "logger1-bucket"
blob_name = "plt-34/logger.json"

# Configure logging
logger = logging.getLogger("my_logger")
handler = logging.handlers.RotatingFileHandler("app.log", maxBytes=2000, backupCount=5)
logger.addHandler(handler)
logger.setLevel(logging.INFO)  # Set logging level to INFO

# Load the keys from the JSON file
with open("/home/bryan/.keys/api_keys.json", "r") as file:
    keys = json.load(file)

# Set environmental variables for AmbientAPI
os.environ["AMBIENT_ENDPOINT"] = "https://api.ambientweather.net/v1"
os.environ["AMBIENT_API_KEY"] = keys["ambient"]["apiKey"]
os.environ["AMBIENT_APPLICATION_KEY"] = keys["ambient"]["applicationKey"]
mac_address = keys["ambient"]["macAddress"]

try:
    # Initialize the API
    api = AmbientAPI()
    logger.info("Initialized AmbientAPI")

    # Get a list of devices (each device is an instance of AmbientWeatherStation)
    devices = api.get_devices()
    logger.info(f"Found {len(devices)} devices")

    # Find the device with the matching MAC address
    device = next(
        (device for device in devices if device.info.get("macAddress") == mac_address),
        None,
    )

    if device is None:
        logger.error(f"No device found with MAC address: {mac_address}")
    else:
        logger.info(f"Using device with MAC address: {mac_address}")

        time.sleep(1)  # Pause for a second to avoid API limits

        # Get data for the device
        data = device.get_data()
        logger.info(f"Got data: {data}")

        # Generate BigQuery schema from data
        schema = gcloud.get_schema(data)
        logger.info(f"Generated schema: {schema}")

        # Update the BigQuery table with data
        gcloud.update_bqtable(schema, data, project_id, dataset_id, table_id)
        logger.info("Updated BigQuery table")

        # Update the bucket
        gcloud.update_bucket(bucket_name, blob_name, local_file)
        logger.info("Updated bucket")

except Exception as e:
    logger.error("Error occurred: ", exc_info=True)
