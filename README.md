# Datalogger2Cloud

Datalogger2Cloud is a system for cloud-integrated automated datalogging for remotely deployed environmental sensors. It utilizes a Raspberry Pi with Raspbian to collect data from a Campbell CR800 datalogger and upload it to Google BigQuery for storage and analysis.

## Introduction

Environmental monitoring often requires collecting data from sensors deployed in remote locations. Traditional dataloggers store data locally, requiring manual retrieval and processing. Datalogger2Cloud addresses this challenge by automating data collection, processing, and uploading to the cloud, enabling real-time access and analysis.

This project focuses on the development and implementation of the software components responsible for data acquisition from the CR800 datalogger, data processing and averaging, and uploading data to Google BigQuery and local storage. The system is designed to operate autonomously in remote locations, powered by a solar-powered battery and utilizing a cellular network for internet connectivity.

## System Components

The Datalogger2Cloud system utilizes several Python scripts:

* **`main_query.py`:** This script is the main driver of the system. It connects to the CR800 datalogger, identifies data tables, determines appropriate data collection intervals, retrieves data, merges it with sensor data from SDI-12 sensors, calculates rolling averages, uploads processed data to BigQuery, and stores data locally in an SQLite database for backup.

* **`logger_query_functions.py`:** This script contains functions used by `main_query.py` for communicating with the datalogger, extracting and processing data, and determining data collection intervals.

* **`gcloud_functions.py`:** This script handles interactions with Google Cloud services, including uploading data to BigQuery, generating BigQuery schema based on the data structure, and retrieving the latest entry time from BigQuery to determine data collection intervals.

* **`database_functions.py`:** This script manages the local SQLite database, including creating the database schema, inserting data, and retrieving the latest timestamp.

* **`setup.py`:** This script automates the setup process on a new Raspberry Pi, installing necessary software packages and configuring systemd services and timers to run the data collection and processing scripts automatically.

## Benefits and Advantages

Datalogger2Cloud offers several advantages over traditional datalogging systems:

* **Automation:** The system automates data collection, processing, and uploading, reducing manual effort and minimizing data loss.

* **Real-time access:** By uploading data to Google BigQuery, the system enables real-time monitoring and analysis of environmental data through cloud storage.

* **Remote deployment:** Datalogger2Cloud is designed to operate autonomously in remote locations, facilitating data collection from inaccessible areas.

* **Data security:** The use of Google BigQuery provides secure and reliable data storage.

* **Backup and redundancy:** The system stores data locally in an SQLite database for backup and redundancy in case of internet connectivity issues.

## Future Directions

While Datalogger2Cloud provides a robust solution for automated datalogging and cloud integration, there are several potential areas for future development and improvement:

* **Expanding sensor compatibility:** The system could be extended to integrate additional sensor types and communication protocols.

* **Data visualization and analysis tools:** Developing dashboards and tools for visualizing and analyzing data stored in BigQuery would enhance the usability and value of the system.

* **Machine learning and anomaly detection:** Implementing machine learning algorithms for data analysis and anomaly detection could provide additional insights and automate the identification of unusual or significant events.

* **Edge computing:** Exploring edge computing techniques for data processing and analysis at the data collection site could reduce data transmission requirements and enable faster response times.


## Repository Contents

This repository contains the source code, configuration files, and documentation for the Datalogger2Cloud system. Please note that this project is a research effort conducted in a lab setting and may require additional configuration and optimization for use in other environments.

Due to its in-progress nature and highly customized needs, I'm not expecting any contributions to the main branch, but you may fork it if you find any part useful. This project is licensed under the MIT License - see the `LICENSE.md` file for details.
```
