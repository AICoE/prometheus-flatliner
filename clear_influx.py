from influxdb import InfluxDBClient
import os
import logging

def main():

    # Set up logging
    _LOGGER = logging.getLogger(__name__)

    if os.getenv("FLT_DEBUG_MODE", "False") == "True":
        logging_level = logging.DEBUG  # Enable Debug mode
    else:
        logging_level = logging.INFO
    # Log record format
    logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', level=logging_level)

    # clean influxdb
    flt_influx__db_dsn = os.getenv("FLT_INFLUX_DB_DSN", "influxdb://username:password@localhost:8086")
    flt_influx_db_name = os.getenv("FLT_INFLUX_DB_NAME", "flatliners")

    client = InfluxDBClient.from_dsn(flt_influx__db_dsn)
    _LOGGER.info("connecting to influxdb...")
    client.drop_database(flt_influx_db_name)
    _LOGGER.info("dropping existing flatliners database")
    client.create_database(flt_influx_db_name)


if __name__ == '__main__':
    main()