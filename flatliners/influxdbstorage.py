from datetime import datetime

from influxdb import InfluxDBClient

from .baseflatliner import BaseFlatliner


class InfluxdbStorage(BaseFlatliner):
    def __init__(self, influx_dsn):
        super().__init__()
        self.influx_dsn = influx_dsn
        self.client = InfluxDBClient.from_dsn(self.influx_dsn, timeout=5)

    def on_next(self, x):
        """ update l2 distance between cluster vector and baseline vector
        """

        print(x)
        self.client.write_points(
            [
                {
                    "measurement": "clusterdata",
                    "tags": {
                        "clusterID": x.cluster
                    },
                    "time": datetime.utcfromtimestamp(x.std_dev_timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "fields": {
                        "weirdness_score": x.weirdness_score

                    }
                }
            ]
        )
