from datetime import datetime
from influxdb import InfluxDBClient
import flatliners
import logging

from .baseflatliner import BaseFlatliner

# Set up logging
_LOGGER = logging.getLogger(__name__)


class InfluxdbStorage(BaseFlatliner):
    def __init__(self, influx_dsn):
        super().__init__()
        self.influx_dsn = influx_dsn
        self.client = InfluxDBClient.from_dsn(self.influx_dsn, timeout=30)
        self.buffer_list = []
        self.buffer_size = 1000
        _LOGGER.info("InfluxDB connection initialized.")

    def on_next(self, x):
        """ update l2 distance between cluster vector and baseline vector
        """
        if isinstance(x, flatliners.weirdnessscore.WeirdnessScore.Resource_State):
            self.buffer_list.append({
                "measurement": "clusterdata",
                "tags": {
                    "clusterID": x.cluster,
                    "clusterVersion": x.version
                },
                "time": datetime.utcfromtimestamp(x.std_dev_timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "weirdness_score": x.weirdness_score
                    }
                })

            self.add_resource_metrics(x)

            if len(self.buffer_list) > self.buffer_size:
                try:
                    self.flush_buffer()
                except:
                    _LOGGER.exception("Failed to flush Influx Buffer. Buffer size:{0}".format(len(self.buffer_list)))

    def flush_buffer(self):
        _LOGGER.debug("Flushing Influx buffer data to the DB, buffer size:{0}".format(len(self.buffer_list)))
        self.client.write_points(self.buffer_list)
        self.buffer_list = []

    def add_resource_metrics(self, x):

        resources = list(x.resource_deltas.keys())
        for resource in resources:
            self.buffer_list.append({
                "measurement": "resource_deltas",
                "tags": {
                    "cluster_id": x.cluster,
                    "cluster_version": x.version,
                    "resource_type": resource
                },
                "time": datetime.utcfromtimestamp(x.std_dev_timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "resource_deltas": x.resource_deltas[resource]

                }
            })
