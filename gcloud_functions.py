from google.cloud import storage
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from typing import List, Dict
import datetime
import platform
import pandas as pd
import os
import json
import tempfile
import os
import subprocess


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        return super().default(obj)


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


def write_read(bucket_name: str, blob_name: str, local_file: str) -> None:
    """Write and read a blob from GCS using file-like IO."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    with open(local_file, "r") as from_, blob.open("w") as to_:
        to_.write(from_.read())


def update_bucket(bucket_name: str, blob_name: str, local_file: str) -> None:
    """Send data to cloud."""

    write_read(bucket_name, blob_name, local_file)


from google.cloud import bigquery
from typing import List, Dict
import datetime
import pandas as pd


def get_schema(list_dicts: List[Dict]) -> List[bigquery.SchemaField]:
    """Takes a list of dictionaries as input and generates a BigQuery schema
    with appropriate field names and types."""

    if not list_dicts:
        return []

    # Define a function to determine the BigQuery type
    def get_bq_type(value):
        if isinstance(value, (int, float)):
            return "FLOAT"
        elif isinstance(value, str):
            return "STRING"
        elif isinstance(value, bool):
            return "BOOLEAN"
        elif isinstance(value, bytes):
            return "BYTES"
        elif isinstance(value, (datetime.datetime, pd.Timestamp)):
            return "TIMESTAMP"
        else:
            raise ValueError(f"Unsupported data type: {type(value)}")

    # Get the first dictionary from the list to infer schema
    sample_dict = list_dicts[0]

    # Generate BigQuery schema fields based on the sample dictionary
    schema = [
        bigquery.SchemaField(field_name, get_bq_type(sample_value))
        for field_name, sample_value in sample_dict.items()
    ]

    return schema


def update_bqtable(
    schema: List[bigquery.SchemaField], table_name: str, table_data: List[Dict]
) -> bool:
    """Update the BigQuery table with newly obtained data from the logger."""

    [project_id, dataset_id, table_id] = get_bq_table(table_name)

    bigquery_client = bigquery.Client(project=project_id)

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        autodetect=False,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    # Convert table_data (list of dicts) to newline-delimited JSON format
    table_data_ndjson = "\n".join(JSONEncoder().encode(item) for item in table_data)

    # Write the data to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(table_data_ndjson.encode("utf-8"))
        temp_file_path = temp_file.name

    # Define the table reference using dataset_id and table_id
    table_ref = bigquery_client.dataset(dataset_id).table(table_id)

    try:
        # Load the data from the temporary file into BigQuery
        with open(temp_file_path, "rb") as temp_file:
            load_job = bigquery_client.load_table_from_file(
                temp_file,
                table_ref,
                job_config=job_config,
            )

            # Wait for the load job to complete
            load_job.result()

            print(f"Loaded {load_job.output_rows} rows into {dataset_id}:{table_id}.")

    except Exception as e:
        print("Encountered error while loading table: ", e)
        if hasattr(e, "errors"):
            print("Detailed errors: ", e.errors)
    finally:
        # Remove the temporary file outside of the 'with' block
        os.remove(temp_file_path)

    return True


def get_latest_entry_time(table_name: str):
    [project_id, dataset_id, table_id] = get_bq_table(table_name)

    client = bigquery.Client(project=project_id)

    full_table_id = f"{project_id}.{dataset_id}.{table_id}"

    # Try block to capture NotFound exception in case table does not exist
    try:
        table = client.get_table(full_table_id)

        # Check if TIMESTAMP column exists
        if "TIMESTAMP" not in [field.name for field in table.schema]:
            return None

        # Construct the query
        query = f"SELECT MAX(TIMESTAMP) as latest FROM `{project_id}.{dataset_id}.{table_id}`"

        query_job = client.query(query)
        results = query_job.result()  # Waits for job to complete.

        for row in results:
            if row.latest is not None:
                return row.latest
    except NotFound:
        print(f"Table '{full_table_id}' does not exist. A new table will be created.")
        return None  # Return None if table does not exist

    return None  # Return None if the table exists but doesn't contain any entries


def get_bq_table(table_name):
    # Get the table_id, project_id, and dataset_id for table_name
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
        "span5_sdi12": {
            "project_id": "crop2cloud",
            "dataset_id": "sensor_data",
            "table_id": "span5_sdi12",
        },
        "weather": {
            "project_id": "crop2cloud",
            "dataset_id": "weather_data",
            "table_id": "weather",
        },
    }

    return [
        table_params[table_name]["project_id"],
        table_params[table_name]["dataset_id"],
        table_params[table_name]["table_id"],
    ]


def update_system_time():
    # Set the system clock from a network time server
    subprocess.run(["sudo", "timedatectl", "set-ntp", "true"])
    # Check the current system clock time
    subprocess.run(["timedatectl"])
