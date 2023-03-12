from pycampbellcr1000 import CR1000
import datetime
import traceback
import ndjson
import logger_query_functions as fxns
import gcloud_functions as Gcloud

""" Program using pycampbell library to collect and store data from datalogger 
    See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""

#datalogger = CR1000.from_url('serial:COM5:38400')
datalogger = CR1000.from_url('serial:/dev/ttyUSB0:38400')

# Getting names of tables containing data
table_names = fxns.get_tables(datalogger)

# Create file to store the last data withdrawal date
date_file = "./date.txt"
try:
    time = datalogger.gettime()
    # _____ strip time to get only datetime
    
    with open(date_file, 'w') as f:
        stored_date = f.read()
        exec(stored_date)   # Stores the previous date in a start variable
except FileNotFoundError:
    with open(date_file, 'x') as f:
        start = datalogger.gettime()
        f.write("start = " + str(start)) # Stores the date at which to start
        
        
# start at start time stored in file and stop now. 
stop = datalogger.gettime()

# Pull data from table
table_data = fxns.get_data(datalogger, table_names[1].decode('utf-8'), start, stop)

local_backup = "./CR800data.json"


# Save values to be appended to Bigquery in local file
#try:
#    with open("./data_to_append", 'w') as f:
#except FileNotFoundError:
#    with open("./data_to_append" 'x') as f:
        
        
# Send stored data to GCloud
Gcloud.update_bucket()

# Append data to local backup file
try:
    with open(local_backup, 'w') as f:
        ndjson.dump(table_data,f)
except FileNotFoundError:
    with open(local_backup, 'x') as f:
        ndjson.dump(table_data,f)
