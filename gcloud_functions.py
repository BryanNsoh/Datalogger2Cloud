from google.cloud import storage
from google.cloud import bigquery
from typing import List, Dict
import os
import json
import tempfile

# Load the keys from the JSON file
with open("/home/bryan/.keys/api_keys.json", "r") as file:
    keys = json.load(file)

# Access keys for google service
google_creds = keys["google"]["application_credentials"]

# Set environment variable for Google credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = google_creds


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


def get_schema(list_dicts: List[Dict]) -> List[bigquery.SchemaField]:
    """Takes a list of dictionaries as input and generates a BigQuery schema
    with appropriate field names and types."""

    if not list_dicts:
        return []

    # Define a mapping of Python data types to BigQuery data types
    type_mapping = {
        int: "INTEGER",
        float: "FLOAT",
        str: "STRING",
        bool: "BOOLEAN",
        bytes: "BYTES",
    }

    # Get the first dictionary from the list to infer schema
    sample_dict = list_dicts[0]

    # Generate BigQuery schema fields based on the sample dictionary
    schema = [
        bigquery.SchemaField(field_name, type_mapping[type(sample_value)])
        for field_name, sample_value in sample_dict.items()
    ]

    return schema


def update_bqtable(
    schema: List[bigquery.SchemaField],
    table_data: List[Dict],
    project_id: str,
    dataset_id: str,
    table_id: str,
) -> bool:
    """Update the BigQuery table with newly obtained data from the logger."""

    bigquery_client = bigquery.Client(project=project_id)

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        autodetect=False,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    # Convert table_data (list of dicts) to newline-delimited JSON format
    table_data_ndjson = "\n".join(json.dumps(item) for item in table_data)

    # Write the data to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(table_data_ndjson.encode("utf-8"))
        temp_file_path = temp_file.name

    # Define the table reference using dataset_id and table_id
    table_ref = bigquery_client.dataset(dataset_id).table(table_id)

    # Load the data from the temporary file into BigQuery
    with open(temp_file_path, "rb") as temp_file:
        load_job = bigquery_client.load_table_from_file(
            temp_file,
            table_ref,
            job_config=job_config,
        )

        # Wait for the load job to complete
        load_job.result()

        # Remove the temporary file
        os.remove(temp_file_path)

        print(f"Loaded {load_job.output_rows} rows into {dataset_id}:{table_id}.")

        return True
