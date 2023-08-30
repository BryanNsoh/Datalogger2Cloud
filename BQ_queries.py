from google.cloud import bigquery
from google.api_core.exceptions import NotFound
import platform
import json
import os

if platform.system() == "Linux":
    # Load the keys from the JSON file
    with open("/home/bryan/.keys/api_keys.json", "r") as file:
        keys = json.load(file)

    # Access keys for google service
    google_creds = keys["google"]["application_credentials"]

    # Set environment variable for Google credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds

elif platform.system() == "Windows":
    # Set environment variable for Google credentials
    os.environ[
        "GOOGLE_APPLICATION_CREDENTIALS"
    ] = r"C:\.keys\crop2cloud-a9f1f94184a4.json"

else:
    raise OSError(
        "Unsupported operating system. This script runs on Linux and Windows only."
    )

# Instantiate a BigQuery client
client = bigquery.Client()

# Specify the details for the tables to be modified
table_params = {
    "span2nodeB": {
        "project_id": "crop2cloud",
        "dataset_id": "sensor_data",
        "table_id": "span2nodeB",
    },
    "span2nodeC": {
        "project_id": "crop2cloud",
        "dataset_id": "sensor_data",
        "table_id": "span2nodeC",
    },
    "span2nodeA": {
        "project_id": "crop2cloud",
        "dataset_id": "sensor_data",
        "table_id": "span2nodeA",
    },
    "span5_all": {
        "project_id": "crop2cloud",
        "dataset_id": "sensor_data",
        "table_id": "span5_all",
    },
    "weather": {
        "project_id": "crop2cloud",
        "dataset_id": "weather_data",
        "table_id": "weather",
    },
}

for table in table_params.values():
    # Construct the full table identifiers
    source_table_id = f"{table['project_id']}.{table['dataset_id']}.{table['table_id']}"
    destination_table_id = (
        f"{table['project_id']}.{table['dataset_id']}.{table['table_id']}_new"
    )

    # Check if dataset exists
    dataset_id = f"{table['project_id']}.{table['dataset_id']}"
    try:
        client.get_dataset(dataset_id)
    except NotFound:
        # If dataset does not exist, create a new one
        client.create_dataset(dataset_id)

    # Check if table exists
    try:
        client.get_table(source_table_id)
        table_exists = True
    except Exception as e:
        table_exists = False

    if table_exists:
        # If table exists, create a new table with data from the original table,
        # renaming the Datetime column to TIMESTAMP
        sql = f"""
        CREATE OR REPLACE TABLE `{destination_table_id}`
        PARTITION BY TIMESTAMP
        AS SELECT
            Datetime AS TIMESTAMP,
            *
        FROM `{source_table_id}`
        """
        # Run the command
        client.query(sql)

        # Now, drop the old table and rename the new one
        # Note: this is a destructive operation. Ensure you have backups or are operating on non-production data
        sql = f"""
        DROP TABLE `{source_table_id}`;
        ALTER TABLE `{destination_table_id}`
        RENAME TO `{source_table_id}`;
        """
        # Run the command
        client.query(sql)
    else:
        # If table does not exist, create a new empty table with TIMESTAMP column
        schema = [
            bigquery.SchemaField("TIMESTAMP", "TIMESTAMP")
        ]  # adjust this to match the schema of your table
        table = bigquery.Table(source_table_id, schema=schema)
        table = client.create_table(table)
