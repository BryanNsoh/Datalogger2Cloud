from datetime import datetime
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

    local_file = "./CR800data.json"
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


def get_start_time():
    """Gets the time to start and stop collecting data"""


def track_and_manage_time(datalogger, delay=60):
    """ "Returns the appropriate start and stop time for data collection"""
    timekeeper_file = os.path.join(os.getcwd(), "./timekeeper.txt")

    # If timekeeper file exists, start collection at stored time and end now
    if os.path.exists(timekeeper_file):
        with open(timekeeper_file, "r") as f:
            stored_datetime_str = f.read().strip()
            stored_datetime = parse_datetime_input(stored_datetime_str)
            if stored_datetime is None:
                print("Invalid datetime in timekeeper file.")
                sys.exit(1)
            start = stored_datetime
            stop = datalogger.gettime()
    # Else, create timekeeper file and collect all data until now
    else:
        with open(timekeeper_file, "x") as f:
            pass
        start = None
        stop = None

    # Set next data collection time to current time
    with open(timekeeper_file, "w") as f:
        next_start = datalogger.gettime()
        f.write(next_start.isoformat())

    return start, stop
