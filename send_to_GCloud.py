# Imports the Google Cloud client library
from google.cloud import storage
import os
import ndjson

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/apt-rite-378417-db62f3c0bfd6.json"

local_file = "/CR800data.json"
bucket_name = "logger1-bucket"
blob_name = "plt-34/logger.json"
    
def write_read(bucket_name, blob_name):
    """Write and read a blob from GCS using file-like IO"""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Mode can be specified as wb/rb for bytes mode.
    # See: https://docs.python.org/3/library/io.html
    
    with open(local_file, "r") as from_, blob.open("w") as to_:
        to_.write(from_.read())

def send_to_cloud():
    """Send data to cloud"""
    write_read(bucket_name, blob_name)
    
