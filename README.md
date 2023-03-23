# Datalogger2Cloud

Datalogger2Cloud is a system designed to collect data from a Campbell CR800 datalogger using a single-board computer running linux connected to a solar-powered battery and a cellular network. The data is then uploaded to Google BigQuery for storage and analysis. This guide will help you set up the entire system on a new linux computer using an automated Python script. If you wish to do a manual setup, please refer to the [manual setup guide](manual_setup.md)

## Overview

The system consists of four Python programs:

1. `main_query.py:` Collects data from the datalogger and uploads it to Google BigQuery.
2. `logger_query_functions.py:` Contains functions for handling data collection and communication with the datalogger.
3. `gcloud_functions.py`: Handles communication with Google Cloud services, including uploading data to BigQuery.
4. `setup.py`: Sets up the system on a new linux computer

## Prerequisites

- Single-board computer running a Linux operating system
- Campbell CR800 datalogger
- Solar-powered battery
- Cellular network connection
- Python 3 installed

## Setup

### 1. Prepare the Hardware

Set up the linux, the Campbell CR800 datalogger, the solar-powered battery, and the cellular network connection according to their respective user guides.

### 2. Run the Automated Setup Script

The provided `setup.py` script automates most of the setup process. First, download the script to your Raspberry Pi. Then, open a terminal, navigate to the directory containing the script, and run the following command:

    sudo python3 setup.py

Enter your password when prompted. The script will create and activate a virtual environment, install necessary packages, create required files, and configure the linux computer to run the `main_query.py` script on startup after an internet connection has been established.

**Note:** You can modify *project_path* and *venv_path* in the `setup.py` script with different paths if you wish. Otherwise, *project_path* will be set to the same directory as `setup.py` and *venv_path* will be set to `~/logger_env`

## Conclusion

This guide should enable a non-technical user to set up the Datalogger2Cloud system on a new linux computer using the automated `setup.py` script. The system will collect data from a Campbell CR800 datalogger, upload it to Google BigQuery, and operate autonomously with a solar-powered battery and a cellular network connection.
