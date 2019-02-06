# Prometheus Flatliner

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/1b26f3bfc4844c61bbc6e3ccbc61c8b2)](https://app.codacy.com/app/AICoE/prometheus-flatliner?utm_source=github.com&utm_medium=referral&utm_content=AICoE/prometheus-flatliner&utm_campaign=Badge_Grade_Settings)

streaming prometheus metric processing

## Getting Started
### Two different modes of operation
This app has two modes of operation,
* Historic data mode
* Live data mode
#### Historic data mode
In this mode, the app collects and analyzes metric data between the range specified using the env vars `FLT_METRIC_START_DATETIME` and `FLT_METRIC_END_DATETIME` for data range start and end respectively.
For example, if you set `FLT_METRIC_START_DATETIME= 5 December 2018 21:00` and `FLT_METRIC_END_DATETIME= 6 December 2018 21:00`, the app will collect and analyze metric data between 5 December 2018 21:00 and 6 December 2018 21:00, more specifically, between `1544043600.0` and `1544130000.0` unix timestamps.
#### Live data mode
In this mode, the app never exits (unless in case of an error) and keeps collecting and analyzing current data from Prometheus.
To enable this mode, `FLT_LIVE_METRIC_COLLECT` should be set to `True`, otherwise it will default to Historic data mode.


### Setting up the virtual environment

*You don't need to set up the virtual environment if you are planning to run the app only on OpenShift, it is done in the image build templates already*

To run this application locally you will need to install several dependencies listed in the pipfile.

These dependencies can be installed in a python virtual environment by running the following command in the root directory for this repository:
```
pipenv install
```

### Setting up the required variables

After the virtual environment has been set up with all the dependencies, create a file with all the required environment variables to run this app. An example env file ([.env.example](https://github.com/AICoE/prometheus-flatliner/blob/master/.env.example)) is included in the repository.

There is also a Makefile in the repository for making it easier to run the application,
open the Makefile and you will see a variable `ENV_FILE` in the beginning, set it to the location of the env variable file that you just created.

### Running on a local machine

After setting up the `ENV_FILE` variable in your Makefile, run the following command

```
make run_app
```
This will start the metrics analysis and store the data to the InfluxDB store (specified using [this variable](https://github.com/AICoE/prometheus-flatliner/blob/master/.env.example#L8)).

### Deploying on OpenShift
Assuming you have the oc client installed and set up.
#### Historic job on OpenShift
After setting up the `ENV_FILE` variable in your Makefile, run the following command

```
make oc_create_build
```
This will create an image stream that will pull this application directly from [Here](https://github.com/AICoE/prometheus-flatliner.git).
Then run
```
make oc_trigger_build
```
This will trigger a new container image build. After the image is built, run the following command to deploy a historic job on OpenShift.
```
make oc_historic_job
```
If you want to cancel the job and delete the container, run the following command:
```
make oc_delete_historic_job
```
This will delete the deployed container
#### Live data collection deployment
After setting up the `ENV_FILE` variable in your Makefile, run the following command

```
make oc_live_deploy
```
This will create a deployment of this app which will keep running according to the specified configuration.

To delete this deployment, run the following command:
```
make oc_delete_live_deployment
```

## Built With

* [rx](https://pypi.org/project/Rx/) - An API for asynchronous programming
with observable streams
* [InfluxDB-Python](https://pypi.org/project/influxdb/) - InfluxDB-Python is a client for interacting with InfluxDB.
* [dateparser](https://dateparser.readthedocs.io/en/latest/) - python parser for human readable dates
* [pandas](http://pandas.pydata.org/) - High Performance Data Structure
* [apscheduler](https://apscheduler.readthedocs.io/en/latest/) - Python Scheduling library
* [retrying](https://github.com/rholder/retrying) - Retrying is a general-purpose retrying library
* [dataclasses](https://www.python.org/dev/peps/pep-0557/) - Data Classes can be thought of as "mutable namedtuples with defaults"
<!-- * [prometheus_client](https://github.com/prometheus/client_python) - Official Python client for Prometheus -->
<!-- * [flask](http://flask.pocoo.org/) - A lightweight web application framework -->
