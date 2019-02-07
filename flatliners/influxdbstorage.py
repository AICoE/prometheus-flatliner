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
        self.buffer_size = 5000
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

            self.buffer_list.append({
                "measurement": "resource_deltas",
                "tags": {
                    "cluster_id": x.cluster,
                    "cluster_version": x.version,
                    "resource_type": x.resource
                },
                "time": datetime.utcfromtimestamp(x.std_dev_timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "resource_deltas": x.resource_deltas[x.resource]

                }
            })


        if isinstance(x, flatliners.weirdnessscore.WeirdnessScore.Alert_Sate):
            # add weirdness score
            self.buffer_list.append({
                "measurement": "alert_frequency_weirdness",
                "tags": {
                    "clusterID": x.cluster,
                    "clusterVersion" : x.version
                },
                "time": datetime.utcfromtimestamp(x.timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields" : {
                    "alert_weirdness_score": x.weirdness_score
                }
            })
            # add relevant resource delta
            self.buffer_list.append({
                "measurement": "alert_delta",
                "tags": {
                    "clusterID": x.cluster,
                    "clusterVersion": x.version, 
                    "alert_type": x.alert
                },
                "time": datetime.utcfromtimestamp(x.timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "alert_deltas": x.alert_deltas[x.alert]
                }
            })

        if len(self.buffer_list) > self.buffer_size:
            try:
                self.flush_buffer()
            except:
                _LOGGER.exception("Failed to flush Influx Buffer. Buffer size:{0}".format(len(self.buffer_list)))

    def flush_buffer(self):
        _LOGGER.debug("Flushing Influx buffer data to the DB, buffer size:{0}".format(len(self.buffer_list)))
        self.client.write_points(self.buffer_list)
        self.buffer_list = []

