from pycampbellcr1000 import CR1000
import datetime
import traceback
import ndjson
import logger_query_functions as fxns
import send_to_GCloud as GCloud

""" Program using pycampbell library to collect and store data from datalogger 
    See here for documentation: https://pycampbellcr1000.readthedocs.io/en/latest/index.html
"""

datalogger = CR1000.from_url('serial:COM5:38400')
#datalogger = CR1000.from_url('serial:/dev/ttyUSB0:38400')

# Getting names of tables containing data
table_names = fxns.get_tables(datalogger)
    

start = datetime.datetime(2022, 8, 30 , 16, 0, 0)
stop = datetime.datetime(2022, 8, 30 , 22, 0, 0)

# Getting data to be stored
table_data = fxns.get_data(datalogger, table_names[1].decode('utf-8'), start, stop)

local_file = r"C:\Users\Bryan\OneDrive - University of Nebraska-Lincoln\Documents\Research\Datalogger Cellular\Data Files\CR800data.json"

try:
    with open(local_file, 'w') as f:
        ndjson.dump(table_data,f)
except FileNotFoundError:
    with open(local_file, 'x') as f:
        ndjson.dump(table_data,f)

#send stored data to GCloud
GCloud.send_to_cloud()
    
local_file = r"C:\Users\Bryan\OneDrive - University of Nebraska-Lincoln\Documents\Research\Datalogger Cellular\Data Files\CR800data.json"

try:
    with open(local_file, 'w') as f:
        ndjson.dump(table_data,f)
except FileNotFoundError:
    with open(local_file, 'x') as f:
        ndjson.dump(table_data,f)
