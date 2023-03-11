from pycampbellcr1000 import CR1000
import datetime
import traceback
import ndjson
import logger_query_functions as fxns
import send_to_GCloud as GCloud

""" Program using pycampbell library to collect and store data from datalogger 
    See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""

#datalogger = CR1000.from_url('serial:COM5:38400')
datalogger = CR1000.from_url('serial:/dev/ttyUSB0:38400')

# Getting names of tables containing data
table_names = fxns.get_tables(datalogger)

# Create file to store the last data withdrawal date
date_file = "/date.txt"
try:
    time = device.gettime()
    # _____ strip time to get only datetime
    
    with open(date_file, 'w') as f:
        stored_date = f.read()
        exec(stored_date)   # Stores the previous date in a start variable
except FileNotFoundError:
    with open(date_file, 'x') as f:
        start = device.gettime()
        f.write("start = " + str(start)) # Stores the date at which to start
        
        
# start at start time stored in file and stop now. 
stop = device.gettime()

# Pull data from table
table_data = fxns.get_data(datalogger, table_names[1].decode('utf-8'), start, stop)

local_backup = "/CR800data.json"
to_Gcloud = ""


# Save values to be appended to Bigquery in local file
try:
    with open(local_file, 'w') as f:
        ndjson.dump(table_data,f)
except FileNotFoundError:
    with open(local_file, 'x') as f:
        ndjson.dump(table_data,f)
        
# Send stored data to GCloud
GCloud.send_to_cloud()

# Append data to local backup file
try:
    with open(local_backup, 'w') as f:
        ndjson.dump(table_data,f)
except FileNotFoundError:
    with open(local_backup, 'x') as f:
        ndjson.dump(table_data,f)
