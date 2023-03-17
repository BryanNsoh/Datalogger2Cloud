# Imports the Google Cloud client library
from google.cloud import storage
from google.cloud import bigquery
from typing import List, Dict
import os
import json
import tempfile

# Retreiving service account key using key_location.txt stored on local machine
file_path = "~/keys/key_location.txt"
expanded_file_path = os.path.expanduser(
    file_path
)  # Replacing the ~ character with the expanded file name
print(expanded_file_path)
with open(expanded_file_path, "r") as f:
    key = f.read()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key

# Paths for google cloud
local_file = "./CR800data.json"
bucket_name = "logger1-bucket"
blob_name = "plt-34/logger.json"

# ID's for BigQuery
project_id = "apt-rite-378417"
dataset_id = "apt-rite-378417.loggertest1"
table_id = "apt-rite-378417.loggertest1.SDIC"


def write_read(bucket_name, blob_name):
    """Write and read a blob from GCS using file-like IO"""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Mode can be specified as wb/rb for bytes mode.
    # See: https://docs.python.org/3/library/io.html

    with open(local_file, "r") as from_, blob.open("w") as to_:
        to_.write(from_.read())


def update_bucket():
    """Send data to cloud"""

    write_read(bucket_name, blob_name)


def get_schema(list_dicts: List[Dict]) -> List[bigquery.SchemaField]:
    """
    Generate BigQuery schema for a list of dictionaries.

    This function takes a list of dictionaries as input and generates a BigQuery schema
    with appropriate field names and types.

    Args:
        list_dicts (List[Dict])-: A list of dictionaries with data.

    Returns:
        List[bigquery.SchemaField]: A list of BigQuery schema fields.
    """

    if not list_dicts:
        return []

    # Define a mapping of Python data types to BigQuery data types
    type_mapping = {
        int: "INTEGER",
        float: "FLOAT",
        str: "STRING",
        bool: "BOOLEAN",
        bytes: "BYTES",
        # Add more mappings if needed
    }

    # Get the first dictionary from the list to infer schema
    sample_dict = list_dicts[0]

    # Generate BigQuery schema fields based on the sample dictionary
    schema = [
        bigquery.SchemaField(field_name, type_mapping[type(sample_value)])
        for field_name, sample_value in sample_dict.items()
    ]

    return schema


def update_bqtable(schema, table_data):
    """Update the bigquery table with newly obtained data from the logger"""

    bigquery_client = bigquery.Client()

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
