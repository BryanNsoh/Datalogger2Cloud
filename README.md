# Datalogger2Cloud

A program using a Raspberry Pi running Raspbian to remotely download data from a Campbell datalogger and send it to the cloud.

## Purpose

The purpose of this program is to collect data from a Campbell CR800 datalogger, upload it to Google BigQuery, and operate autonomously with a solar-powered battery and a cellular network connection.

## Setup

### 1. Install and Upgrade Python Modules

Open a terminal on your Raspberry Pi and run the following commands:

#### Create a virtual environment
    `python3 -m venv venv`
#### Activate the virtual environment
    `source venv/bin/activate`
#### Upgrade pip
    `pip install --upgrade pip`
#### Install required packages
    `pip install pycampbellcr1000 pandas ndjson`
#### Upgrade google-cloud-storage
    `pip install --upgrade google-cloud-storage`
#### Install google-cloud-bigquery
    `pip install --upgrade google-cloud-bigquery`


### 2. Set up the Proper Shutdown and Restart Routines

#### 2.1. Configure the Raspberry Pi to Shut Down after Running the Python Script

Edit the `basic_query.py` script to include the following line at the end of the script: `os.system("sudo shutdown -h now")`. 


This line will shut down the Raspberry Pi after the script has finished executing.

#### 2.2. Configure the Raspberry Pi to Automatically Update the Time from the Internet

To ensure the Raspberry Pi's clock stays accurate, install the `ntp` package by running the following command: `sudo apt-get install ntp`


#### 2.3. Configure the Raspberry Pi to Run the Python Script on Startup

1. **Edit the `rc.local` file**: Open the `rc.local` file using the following command: `sudo nano /etc/rc.local`

2. **Add the following line before the `exit 0` line**: `/path/to/your/venv/bin/python /path/to/your/project/basic_query.py` & Replace `/path/to/your/venv` with the path to the virtual environment you created earlier, and `/path/to/your/project` with the path to the directory containing your Python files.

3. **Save and close the file**: Press `CTRL + X`, then `Y`, and then `Enter` to save the changes and close the file.

4. **Install the `rtcwake` utility and schedule hourly restarts**: To make the Raspberry Pi restart at the beginning of every hour and shut down after running the Python script, install the `rtcwake` utility by running the following command: `sudo apt-get install rtcwake`


5. **Create a shell script to schedule hourly restarts**: Create a new file called `hourly_restart.sh` in your project directory with the following content:

    ```bash
    #!/bin/bash
    while true; do
    rtcwake -m no -s $(( 60 - $(date +%s) % 60 ))
    sleep 60
    done 
    ```
    This script will make the Raspberry Pi sleep until the beginning of every hour.

6. **Make the shell script executable**: Run the following command to make the script executable: `chmod +x /path/to/your/project/hourly_restart.sh`. Replace `/path/to/your/project` with the path to the directory containing your Python files.

7. **Add the shell script to the `rc.local` file**: Edit the `rc.local` file again using the following command: `sudo nano /etc/rc.local`. Then add the following line before the `exit 0` line: `/path/to/your/project/hourly_restart.sh` & Replace `/path/to/your/project` with the path to the directory containing your Python files.

8. **Save and close the file**: Press `CTRL + X`, then `Y`, and then `Enter` to save the changes and close the file.
Now the Raspberry Pi will restart at the beginning of every hour, run the Python script to collect and upload data, and shut down after the script has finished executing.

## Optional: Add Images
You can add images to the README.md file by uploading them to a hosting service and using the following Markdown syntax: `![Image description](https://example.com/image-url)`. Replace `Image description` with a description of the image, and `https://example.com/image-url` with the URL of the uploaded image.


## Conclusion

By following this guide, you have set up a Raspberry Pi to run the Datalogger2Cloud system. The system consists of three Python scripts: `logger-query_functions.py`, `gcloud_functions.py`, and `basic_query.py`. These scripts collect data from a Campbell datalogger and upload it to Google Cloud BigQuery. The Raspberry Pi will restart at the beginning of every hour, run the Python script to collect and upload data, and shut down after the script has finished executing.

The installation process involved setting up a virtual environment, installing and upgrading the necessary Python modules, and configuring the Raspberry Pi to restart at the beginning of every hour and run the Python script after establishing an internet connection.

With the Datalogger2Cloud system in place, you can collect and analyze data from your Campbell datalogger remotely and with minimal human intervention. If you encounter any issues or have suggestions for improvements, feel free to contribute to the project on GitHub.




