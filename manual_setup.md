# Datalogger2Cloud

Datalogger2Cloud is a system designed to collect data from a Campbell CR800 datalogger using a Raspberry Pi running Raspbian connected to a solar-powered battery and a cellular network. The data is then uploaded to Google BigQuery for storage and analysis. This guide will help you set up the entire system on a new Raspberry Pi.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Setup](#setup)
    1. [Install and Upgrade Python Modules](#install-and-upgrade-python-modules)
    2. [Set up the Proper Shutdown and Restart Routines](#set-up-the-proper-shutdown-and-restart-routines)
4. [Optional: Add Images](#optional-add-images)
5. [Testing and Validation](#testing-and-validation)
6. [Maintenance and Updates](#maintenance-and-updates)
7. [Troubleshooting](#troubleshooting)
8. [Conclusion](#conclusion)

## Overview <a name="overview"></a>

The system consists of three Python programs:

1. `main_query.py:` Collects data from the datalogger and uploads it to Google BigQuery.
2. `logger_query_functions.py:` Contains functions for handling data collection and communication with the datalogger.
3. `gcloud_functions.py`: Handles communication with Google Cloud services, including uploading data to BigQuery.

## Prerequisites <a name="prerequisites"></a>

- Raspberry Pi (Model 3 or newer recommended)
- Raspbian or another compatible Linux operating system
- Campbell CR800 datalogger
- Solar-powered battery with sufficient capacity for your use case
- Cellular network connection (compatible USB modem or HAT)
- Python 3 installed

## Setup <a name="setup"></a>

### 1. Install and Upgrade Python Modules <a name="install-and-upgrade-python-modules"></a>

Open a terminal, on your Raspberry Pi and run the following commands:

#### Create a virtual environment 
    python3 -m venv /path/to/your/venv
#### Activate the virtual environment
    source /path/to/your/venv/bin/activate
#### Upgrade pip
    pip install --upgrade pip
#### Install required packages
    pip install pycampbellcr1000 pandas ndjson
#### Upgrade google-cloud-storage
    pip install --upgrade google-cloud-storage
#### Install google-cloud-bigquery
    pip install --upgrade google-cloud-bigquery

Then, navigate to your project directory, create `first_start_flag.txt` and type a single `0`
This file will be used to indicate that the system has been started for the first time.


### 2. Set up the Proper Shutdown and Restart Routines <a name="set-up-the-proper-shutdown-and-restart-routines"></a>

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

<a name="testing-and-validation"></a>
## Testing and Validation

To ensure that the system is functioning correctly, follow these steps:

1. **Verify successful data uploads to Google BigQuery**: Check your BigQuery dashboard to see if new data is being uploaded. The data should appear in the specified table.

2. **Monitor system performance**: Use the `top` command in the terminal to monitor system performance and check for any excessive CPU or memory usage by the Python script.

3. **Check logs**: Review the logs generated by the `systemd` service for any issues or error messages. To view the logs, run the following command: `journalctl -u main_query.service`

<a name="maintenance-and-updates"></a>
## Maintenance and Updates

To keep your system running smoothly and securely, follow these maintenance steps:

1. **Update the operating system**: Regularly update your Raspberry Pi's Raspbian OS with the latest security patches and updates by running the following commands:

    ```
    sudo apt-get update  
    sudo apt-get upgrade
    ```


2. **Update Python packages**: Keep the Python packages up-to-date by running the following commands within your virtual environment:

    ```
    pip install --upgrade pip  
    pip install --upgrade PACKAGE_NAME
    ```


Replace `PACKAGE_NAME` with the name of the package you want to update.

3. **Update the datalogger's firmware**: Check the manufacturer's website for firmware updates for your Campbell CR800 datalogger and follow their instructions to update the firmware.

<a name="troubleshooting-and-error-handling"></a>
## Troubleshooting and Error Handling

If you encounter issues while setting up or running the system, consider the following troubleshooting steps:

1. **Check logs**: Review the logs generated by the `systemd` service for error messages. To view the logs, run the following command: `journalctl -u main_query.service`

2. **Recheck connections**: Verify that all physical connections, such as power and data cables, are properly connected and secure.

3. **Test internet connectivity**: Confirm that your Raspberry Pi can connect to the internet by running the following command: `ping -c 4 google.com`

4. **Validate Python script functionality**: Run the Python scripts individually to check for any issues or errors.

<a name="security-best-practices"></a>
## Security Best Practices

Follow these security best practices to help protect your Raspberry Pi and data:

1. **Change the default password**: Change the default password for the `pi` user by running the `passwd` command.

2. **Update the system**: Keep the Raspberry Pi's Raspbian OS up-to-date by regularly installing the latest security patches and updates.

3. **Configure a firewall**: Set up a firewall to help protect your Raspberry Pi from unauthorized access. You can use the `ufw` (Uncomplicated Firewall) package to configure a basic firewall.

<a name="conclusion"></a>
## Conclusion

This guide should enable a non-technical user to set up the Datalogger2Cloud system on a new Raspberry Pi. The system will collect data from a Campbell CR800 datalogger, upload it to Google BigQuery, and operate autonomously with a solar-powered battery and a cellular network connection.




