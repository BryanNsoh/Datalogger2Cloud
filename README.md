# Datalogger2Cloud

Datalogger2Cloud is a system for cloud-integrated automated datalogging for remotely deployed environmental sensors. It utilizes a Raspberry Pi with Raspbian to collect data from a Campbell CR800 datalogger and upload it to Google BigQuery for storage and analysis. 

## Introduction

This project focuses on the development and implementation of Datalogger2Cloud, specifically the software components responsible for:

* **Data acquisition from the CR800 datalogger.**
* **Data processing and averaging.**
* **Uploading data to Google BigQuery and local storage.**

This system is designed to operate autonomously in remote locations, powered by a solar-powered battery and utilizing a cellular network for internet connectivity. 

## Objectives

The main objectives of this project were:

1. **Develop a reliable and efficient method for collecting data from the CR800 datalogger.**
2. **Implement data processing techniques to average sensor readings over specific time intervals.**
3. **Establish a secure and automated process for uploading data to Google BigQuery for storage and analysis.**
4. **Store data locally for backup and redundancy.**

## Background

Environmental monitoring often requires collecting data from sensors deployed in remote locations. Traditional dataloggers store data locally, requiring manual retrieval and processing. Datalogger2Cloud addresses this challenge by automating data collection, processing, and uploading to the cloud, enabling real-time access and analysis. 

## Methodology

The Datalogger2Cloud system utilizes several Python scripts:

* **`main_query.py`:** This script is responsible for:
    * Connecting to the CR800 datalogger.
    * Identifying data tables within the datalogger.
    * Determining the appropriate start and stop times for data collection based on the latest entry in BigQuery.
    * Retrieving data from the datalogger.
    * Merging data from the datalogger with sensor data collected from SDI-12 sensors.
    * Calculating rolling averages for sensor readings.
    * Uploading the processed data to Google BigQuery.
    * Storing the data locally in an SQLite database for backup.
* **`logger_query_functions.py`:** This script contains functions used by `main_query.py` for:
    * Communicating with the datalogger.
    * Extracting and processing data from the datalogger.
    * Determining appropriate data collection intervals.
* **`gcloud_functions.py`:** This script handles interactions with Google Cloud services, including:
    * Uploading data to BigQuery.
    * Generating BigQuery schema based on the data structure.
    * Retrieving the latest entry time from BigQuery to determine data collection intervals.
* **`database_functions.py`:** This script manages the local SQLite database, including:
    * Creating the database schema based on the data structure.
    * Inserting data into the database.
    * Retrieving the latest timestamp from the database.
* **`setup.py`:** This script automates the setup process on a new Raspberry Pi, including:
    * Installing necessary software packages.
    * Creating and configuring systemd services and timers to run the data collection and processing scripts automatically.

## Results and Findings

Datalogger2Cloud successfully:

* **Collects data from the CR800 datalogger and SDI-12 sensors.**
* **Processes and averages sensor readings.**
* **Uploads data to Google BigQuery and local storage.**
* **Operates autonomously in remote locations.**

The system provides real-time access to environmental data, enabling researchers and practitioners to monitor and analyze environmental conditions remotely. 

## Discussion

Datalogger2Cloud offers several advantages:

* **Automation:** Automates data collection, processing, and uploading, reducing manual effort and minimizing data loss.
* **Real-time access:** Enables real-time monitoring and analysis of environmental data through cloud storage.
* **Remote deployment:** Operates autonomously in remote locations, facilitating data collection from inaccessible areas.
* **Data security:** Utilizes Google BigQuery for secure and reliable data storage.
* **Backup and redundancy:** Stores data locally for backup and redundancy in case of internet connectivity issues.

## Conclusion

Datalogger2Cloud provides a robust and efficient solution for cloud-integrated automated datalogging of environmental sensor data. This system facilitates real-time monitoring and analysis, contributing to improved environmental research and management practices. 

## Future Directions

Future work could focus on:

* **Expanding sensor compatibility:** Integrating additional sensor types and communication protocols.
* **Data visualization and analysis tools:** Developing dashboards and tools for visualizing and analyzing data stored in BigQuery.
* **Machine learning and anomaly detection:** Implementing machine learning algorithms for data analysis and anomaly detection.
* **Edge computing:** Exploring edge computing techniques for data processing and analysis at the data collection site.

This project provides a foundation for further development and customization to meet specific environmental monitoring needs.

## Installation and Setup

For detailed instructions on installing and setting up Datalogger2Cloud on a Raspberry Pi, please refer to the `INSTALL.md` file in this repository. 

## Contributing

Contributions to this project are welcome! Please see the `CONTRIBUTING.md` file for guidelines on how to contribute. 

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.
