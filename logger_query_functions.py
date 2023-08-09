from datetime import datetime, time, timedelta, date
import gcloud_functions as gcloud
import os
import json
import os.path
import math


def get_tables(datalogger):
    """Gets a list of the names of the tables stored in the datalogger"""
    table_names = []
    while True:
        table_names = datalogger.list_tables()
        # For testing
        print("The table names are:")
        print(table_names)

        # If table_names is not empty, break (if statement true if not empty)
        # Otherwise, continue loop
        if table_names:
            return table_names
        else:
            print("Failed to get table names")


def get_data(datalogger, table_name, start, stop):
    table_data = datalogger.get_data(table_name, start, stop)
    cleaned_data = []

    for label in table_data:
        dict_entry = {}
        for key, value in label.items():
            key = key.replace("b'", "").replace("'", "")

            # Convert Datetime key to TIMESTAMP and retain its datetime object value
            if key == "Datetime":
                key = "TIMESTAMP"

            dict_entry[key] = value

            try:
                if math.isnan(value):
                    dict_entry[key] = -9999
            except TypeError:
                continue

        cleaned_data.append(dict_entry)

    # sort the cleaned data by TIMESTAMP
    cleaned_data.sort(key=lambda x: x["TIMESTAMP"])

    return cleaned_data if cleaned_data else []


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def store_in_ndjson(list_dict):
    local_file = "./span2nodeA.ndjson"
    temp_file = "./temp_span2nodeA.ndjson"

    # Load existing data and remember the RecNbr values
    existing_data = []
    existing_recnbrs = set()
    if os.path.exists(local_file):
        with open(local_file, "r") as f:
            for line in f:
                item = json.loads(line)
                existing_data.append(item)
                existing_recnbrs.add(item["TIMESTAMP"])

    # Filter new data, discarding items with TIMESTAMP that already exist
    list_dict = [
        item for item in list_dict if item["TIMESTAMP"] not in existing_recnbrs
    ]

    # Append new data to existing data
    existing_data.extend(list_dict)

    # Write the combined data back to a temporary file
    with open(temp_file, "w") as f:
        for item in existing_data:
            f.write(JSONEncoder().encode(item) + "\n")

    # Replace the old file with the new file
    os.replace(temp_file, local_file)


def parse_datetime_input(input_string):
    try:
        return datetime.fromisoformat(input_string)
    except ValueError:
        return None


def load_last_logged_time(data_file):
    if os.path.exists(data_file):
        try:
            with open(data_file, "r") as f:
                data = list(ndjson.load(f))
                if data:  # if the list is not empty
                    # assuming each dictionary has a 'TIMESTAMP' field with the isoformat time
                    stored_datetime_str = data[-1]["TIMESTAMP"]
                    return parse_datetime_input(stored_datetime_str)
        except Exception as e:
            print(f"An error occurred while loading last logged time: {e}")
    return None


def determine_start_stop(last_logged_time, datalogger):
    if last_logged_time:
        start = last_logged_time
        stop = datalogger.gettime()
    else:
        # use the current date - 2 days as the default start time
        start = datetime.combine(datetime.now().date() - timedelta(days=2), time())
        stop = datalogger.gettime()
    return start, stop


from datetime import timedelta


def track_and_manage_time(datalogger, project_id, dataset_id, table_id, delay=60):
    """Returns the appropriate start and stop time for data collection"""

    # Fetch the timestamp of the latest entry from BigQuery
    last_logged_time = gcloud.get_latest_entry_time(project_id, dataset_id, table_id)

    # If the last logged time exists, increment it by one second
    if last_logged_time is not None:
        start = last_logged_time + timedelta(seconds=1)
    else:
        # use the current date - 2 days as the default start time
        start = datetime.combine(datetime.now().date() - timedelta(days=2), time())

    stop = datalogger.gettime()

    return start, stop
