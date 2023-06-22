from datetime import datetime, time
import os
import sys
import os.path
import math
import ndjson


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
    """Gets the data for a given table in the table_names list. leave blank to get all data"""

    table_data = []
    cleaned_data = []

    table_data = datalogger.get_data(table_name, start, stop)

    # Cleaning table data
    for label in table_data:
        dict_entry = {}
        for key, value in label.items():
            # Removing b' and ' characters from dict keys
            key = key.replace("b'", "")
            key = key.replace("'", "")
            dict_entry[key] = value
            # Converting all datetime objects to ISO-formatted strings
            if isinstance(value, datetime):
                dict_entry[key] = value.isoformat()
            # Converting all NAN entries to -9999
            try:
                if math.isnan(value):
                    dict_entry[key] = -9999
            except TypeError:
                # Continue iterating if the value is not a float
                continue
        cleaned_data.append(dict_entry)

    if cleaned_data:
        return cleaned_data
    else:
        print("No data available")
        return []


def store_in_ndjson(list_dict):
    """Stores a given listdict as ndjson in the current directory"""

    local_file = "./table_data.json"
    try:
        with open(local_file, "w") as f:
            ndjson.dump(list_dict, f)
    except FileNotFoundError:
        with open(local_file, "x") as f:
            ndjson.dump(list_dict, f)


def parse_datetime_input(input_string):
    try:
        return datetime.fromisoformat(input_string)
    except ValueError:
        return None


def load_last_logged_time(timekeeper_file):
    if os.path.exists(timekeeper_file):
        with open(timekeeper_file, "r") as f:
            stored_datetime_str = f.read().strip()
            return parse_datetime_input(stored_datetime_str)
    return None


def save_new_logged_time(timekeeper_file, datalogger):
    with open(timekeeper_file, "w") as f:
        next_start = datalogger.gettime()
        f.write(next_start.isoformat())


def determine_start_stop(last_logged_time, datalogger):
    if last_logged_time:
        start = last_logged_time
        stop = datalogger.gettime()
    else:
        start = datetime.combine(datetime(2023, 7, 19), time())
        stop = datalogger.gettime()
    return start, stop


def track_and_manage_time(datalogger, delay=60):
    """Returns the appropriate start and stop time for data collection"""
    timekeeper_file = os.path.join(os.getcwd(), "./timekeeper.txt")

    # Load the last logged time, if it exists
    last_logged_time = load_last_logged_time(timekeeper_file)

    # If last logged time is invalid and file exists, print an error message and proceed
    if last_logged_time is None and os.path.exists(timekeeper_file):
        print("Invalid datetime in timekeeper file. Collecting all data up to now...")

    # Determine the start and stop times
    start, stop = determine_start_stop(last_logged_time, datalogger)

    # Save the new logged time
    save_new_logged_time(timekeeper_file, datalogger)

    return start, stop
