# Datalogger2Cloud

Datalogger2Cloud is a system designed to collect data from a Campbell CR800 datalogger using a Raspberry Pi running Raspbian connected to a solar-powered battery and a cellular network. The data is then uploaded to Google BigQuery for storage and analysis. This guide will help you set up the entire system on a new Raspberry Pi.

## Overview

The system consists of three Python programs:

1. `main_query.py:` Collects data from the datalogger and uploads it to Google BigQuery.
2. `logger_query_functions.py:` Contains functions used by `main_query.py` for handling data collection and communication with the datalogger.
3. `gcloud_functions.py`: Contains functions used by `main_query.py` for handling communication with Google Cloud services, including uploading data to BigQuery.

## Prerequisites

- Single-board computer running a linux operating system
- Campbell CR800 datalogger
- Solar-powered battery
- Cellular network connection
- Python 3 installed

## Setup

### 1. Create

### 1. Install and Upgrade Python Modules

Open a terminal, on your Raspberry Pi and run the following commands:

#### Create a virtual environment 
    `python3 -m venv /path/to/your/venv`
#### Activate the virtual environment
    `source /path/to/your/venv/bin/activate`
#### Upgrade pip
    `pip install --upgrade pip`
#### Install required packages
    `pip install pycampbellcr1000 pandas ndjson`
#### Upgrade google-cloud-storage
    `pip install --upgrade google-cloud-storage`
#### Install google-cloud-bigquery
    `pip install --upgrade google-cloud-bigquery`

Then, navigate to your project directory, create `first_start_flag.txt` and type a single `0`
This file will be used to indicate that the system has been started for the first time.


### 2. Set up the Proper Shutdown and Restart Routines

#### 2.1. Configure the Raspberry Pi to Shut Down after Running the Python Script

The script `main_query.py` shuts down automatically once it has finished excecuting.

#### 2.2. Configure the Raspberry Pi to Automatically Update the Time from the Internet

To ensure the Raspberry Pi's clock stays accurate, install the `chrony` package by running the following command: `sudo apt-get install chrony`

#### 2.3. Configure the Raspberry Pi to Run the Python Script on Startup after an Internet Connection has been Established

1. **Create a `systemd` service**: Create a new file called `main_query.service` in your project directory with the following content:

    ```
    [Unit]
    Description=Run main_query.py after an Internet connection is established
    Wants=network-online.target
    After=network-online.target

    [Service]
    Type=simple
    User=pi
    ExecStart=/path/to/your/venv/bin/python /path/to/your/project/run_on_connection.sh
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
    ```

    Replace `/path/to/your/venv` with the path to the virtual environment you created earlier, and `/path/to/your/project` with the path to the directory containing your Python files.

2. **Create the `run_on_connection.sh` script**: Create a new file called `run_on_connection.sh` in your project directory with the following content:

    ```bash
    #!/bin/bash
    while true; do
      # Wait for an internet connection
      while ! ping -c 1 -W 1 8.8.8.8; do
        sleep 1
      done

      # Update the system time
      sudo chronyc -a makestep

      # Run the Python script
      /path/to/your/venv/bin/python /path/to/your/project/main_query.py

      # Sleep for an hour
      sleep 3600
    done
    ```

    Replace `/path/to/your/venv` with the path to the virtual environment you created earlier, and `/path/to/your/project` with the path to the directory containing your Python files.

3. **Make the script executable**: Run the following command to make the script executable: `chmod +x /path/to/your/project/run_on_connection.sh`. Replace `/path/to/your/project` with the path to the directory containing your Python files.

4. **Copy the `systemd` service file**: Copy the `main_query.service` file to the `/etc/systemd/system` directory by running the following command: `sudo cp /path/to/your/project/main_query.service /etc/systemd/system/main_query.service`. Replace `/path/to/your/project` with the path to the directory containing your Python files.

5. **Enable the `systemd` service**: Enable the `main_query.service` to start on boot by running the following command: `sudo systemctl enable main_query.service`

6. **Start the `systemd` service**: Start the `main_query.service` immediately by running the following command: `sudo systemctl start main_query.service`

Now the Raspberry Pi will run the Python script to collect and upload data after an internet connection has been established, update the system time, and then sleep for an hour before repeating the process.


## Optional: Add Images
You can add images to the README.md file by uploading them to a hosting service and using the following Markdown syntax: `![Image description](https://example.com/image-url)`. Replace `Image description` with a description of the image, and `https://example.com/image-url` with the URL of the uploaded image.


## Conclusion

This guide should enable a non-technical user to set up the Datalogger2Cloud system on a new Raspberry Pi. The system will collect data from a Campbell CR800 datalogger, upload it to Google BigQuery, and operate autonomously with a solar-powered battery and a cellular network connection.




