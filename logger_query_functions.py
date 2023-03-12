from pycampbellcr1000 import CR1000
import datetime
import csv
import traceback
import os

    
def get_tables(datalogger):
    """Gets a list of the names of the tables stored in the datalogger"""
    table_names = []
    while True:
        try:
            table_names = datalogger.list_tables()
            #For testing
            print("The table names are:")
            print(table_names)
        except Exception:
            # Store exception in a text file in the local directory
            try:
                with open(os.path.join('', 'error_msg.txt'), "x") as err_msg:
                    traceback.print_exc(limit=None,file=err_msg, chain=True)
            except FileExistsError:
                with open(os.path.join('', 'error_msg.txt'), "w") as err_msg:
                    traceback.print_exc(limit=None,file=err_msg, chain=True)
                
        
        # If table_names is not empty, break (if statement true if not empty)
        # Otherwise, continue loop
        if(table_names):
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
                    key = key.replace("b\'", "")
                    key = key.replace("\'", "")
                    dict_entry[key] = value
                    # Converting all datetime objects to ISO-formatted strings
                    if isinstance(value, datetime.datetime):
                        dict_entry[key] = value.isoformat()
                cleaned_data.append(dict_entry) 
                
        except Exception:
            # Store exception in a text file in the local directory
            try:
                with open(os.path.join('', 'error_msg.txt'), "x") as err_msg:
                    traceback.print_exc(limit=None,file=err_msg, chain=True)
            except FileExistsError:
                with open(os.path.join('', 'error_msg.txt'), "w") as err_msg:
                    traceback.print_exc(limit=None,file=err_msg, chain=True)
        
        # If something has been stored in table_data, exit loop.
        # Otherwise, continue
        if(cleaned_data):
            return cleaned_data
        else:
            print("failed to get data")
            
