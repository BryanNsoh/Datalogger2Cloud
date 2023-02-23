# Imports the Google Cloud client library
from google.cloud import storage
import os
import ndjson

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Bryan\OneDrive - University of Nebraska-Lincoln\Documents\Research\Datalogger Cellular\apt-rite-378417-db62f3c0bfd6.json"

local_file = r"C:\Users\Bryan\OneDrive - University of Nebraska-Lincoln\Documents\Research\Datalogger Cellular\Data Files\CR800data.json"
bucket_name = "logger1-bucket"
blob_name = "plt-34/logger.json"
    
    
# Convert Json to NDJson
with open(local_file, "r") as f:
    new_data = []
    old_data = ndjson.load(f)
    #copying old_data listdict into new_data while cutting out b' and ' strings
    for obj in old_data:
        dict_entry = {}
        for key, value in obj.items():
            dict_entry[key] = value
        new_data.append(dict_entry)          
with open(local_file, "w") as f:
    print(new_data)
    ndjson.dump(new_data,f)

def write_read(bucket_name, blob_name):
    """Write and read a blob from GCS using file-like IO"""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    # Mode can be specified as wb/rb for bytes mode.
    # See: https://docs.python.org/3/library/io.html
    
    with open(local_file, "r") as from_, blob.open("w") as to_:
        to_.write(from_.read())

write_read(bucket_name, blob_name)