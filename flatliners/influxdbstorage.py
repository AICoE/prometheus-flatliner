from datetime import datetime
from influxdb import InfluxDBClient

from .baseflatliner import BaseFlatliner


class InfluxdbStorage(BaseFlatliner):
    def __init__(self, influx_dsn):
        super().__init__()
        self.influx_dsn = influx_dsn
        self.client = InfluxDBClient.from_dsn(self.influx_dsn, timeout=5)
        self.buffer_list = []
        self.buffer_size = 500

    def on_next(self, x):
        """ update l2 distance between cluster vector and baseline vector
        """
        self.buffer_list.append({
            "measurement": "clusterdata",
            "tags": {
                "clusterID": x.cluster
            },
            "time": datetime.utcfromtimestamp(x.std_dev_timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields": {
                "weirdness_score": x.weirdness_score

            }
        })

        if len(self.buffer_list) > self.buffer_size:
            self.flush_buffer()

    def flush_buffer(self):
        print("Flushing Buffer Data to the DB") # Keep this for debugging, change to a log entry later
        self.client.write_points(self.buffer_list)
        self.buffer_list = []
