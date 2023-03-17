from pycampbellcr1000 import CR1000
from datetime import timedelta
import traceback
import os
import sys
from datetime import datetime, timedelta
import os.path
import time


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

    while True:

        table_data = []
        cleaned_data = []

        try:
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
                cleaned_data.append(dict_entry)

        except Exception:
            # Store exception in a text file in the local directory
            try:
                with open(os.path.join("", "error_msg.txt"), "x") as err_msg:
                    traceback.print_exc(limit=None, file=err_msg, chain=True)
            except FileExistsError:
                with open(os.path.join("", "error_msg.txt"), "w") as err_msg:
                    traceback.print_exc(limit=None, file=err_msg, chain=True)

        # If something has been stored in table_data, exit loop.
        # Otherwise, continue
        if cleaned_data:
            return cleaned_data
        else:
            print("failed to get data")


def parse_datetime_input(input_string):
    try:
        return datetime.fromisoformat(input_string)
    except ValueError:
        return None


def track_and_manage_time(input_datetime=None, delay=60):
    timekeeper_file = "./timekeeper.txt"

    if input_datetime is not None:
        input_datetime = parse_datetime_input(input_datetime)
        if input_datetime is None:
            print("Invalid datetime input.")
            sys.exit(1)

    if os.path.exists(timekeeper_file):
        with open(timekeeper_file, "r") as f:
            stored_datetime_str = f.read().strip()
            stored_datetime = parse_datetime_input(stored_datetime_str)
            if stored_datetime is None:
                print("Invalid datetime in timekeeper file.")
                sys.exit(1)
            start = stored_datetime
    else:
        # Create the full file path by joining the directory and file name
        full_path = os.path.join(os.getcwd(), timekeeper_file)
        # Create timekeeper file
        with open(full_path, "x") as f:
            pass
        start = input_datetime or datetime.now()

    with open(timekeeper_file, "w") as f:
        stop = start + timedelta(minutes=delay)
        f.write(stop.isoformat())

    # Delay for the given number of minutes
    time.sleep(delay * 60)

    return start, stop
