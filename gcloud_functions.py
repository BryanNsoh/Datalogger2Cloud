# Imports the Google Cloud client library
from google.cloud import storage
from google.cloud import bigquery
import os
import json
import pandas as pd
from pandas_gbq import to_gbq

# Retreiving service account key using key_location.txt stored on local machine
file_path = '~/keys/key_location.txt'
expanded_file_path = os.path.expanduser(file_path)  # Replacing the ~ character with the expanded file name
print(expanded_file_path)
with open(expanded_file_path, 'r') as f:
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
    
    
def update_bqtable(table_data):
    """Update the bigquery table with newly obtained data from the logger"""

    df = pd.DataFrame(table_data)
    bigquery_client = bigquery.Client()

    
    job_config = bigquery.LoadJobConfig(
        schema = [
        bigquery.SchemaField("Datetime", "TIMESTAMP"),
        bigquery.SchemaField("RecNbr", "INTEGER"),
        bigquery.SchemaField("BatV", "FLOAT"),
        bigquery.SchemaField("VWC_1", "FLOAT"),
        bigquery.SchemaField("EC_1", "FLOAT"),
        bigquery.SchemaField("ST_1", "FLOAT"),
        bigquery.SchemaField("P_1", "INTEGER"),
        bigquery.SchemaField("VWC_2", "FLOAT"),
        bigquery.SchemaField("EC_2", "FLOAT"),
        bigquery.SchemaField("ST_2", "FLOAT"),
        bigquery.SchemaField("P_2", "INTEGER"),
        bigquery.SchemaField("VWC_3", "FLOAT"),
        bigquery.SchemaField("EC_3", "FLOAT"),
        bigquery.SchemaField("ST_3", "FLOAT"),
        bigquery.SchemaField("P_3", "INTEGER")
        ],
        autodetect=False,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    )

    # Append the data to the existing BigQuery table
    load_job = bigquery_client.load_table_from_json(table_data, table_id, job_config=job_config)
    
    # Wait for the job to complete
    load_job.result()

    # Print the number of rows inserted
    print(f"{load_job.output_rows} rows inserted to {table_id}")

    