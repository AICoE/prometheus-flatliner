from time import sleep
from collections import defaultdict
from .baseflatliner import BaseFlatliner

from prometheus_client import Gauge, start_http_server

# Set up logging
import logging
_LOGGER = logging.getLogger(__name__)

class PrometheusEndpoint(BaseFlatliner):
    """docstring for PrometheusEndpoint."""
    def __init__(self):
        super().__init__()
        _LOGGER.info("Prometheus Endpoint initialized.")
        self.update_interval = 60 # seconds
        self.metric_buffer = defaultdict(list)
        self.weirdness_score_gauge = Gauge('weirdness_score','Weirdness score for the given Cluster and Version',['cluster','version'])
        self.prev_metric_list = []

    def on_next(self, x):
        try:
            rounded_timestamp = round(float(x.timestamp)/self.update_interval) * self.update_interval
        except Exception as e:
            _LOGGER.error("Couldn't process the following packet {0}. Reason: {1}".format(x,str(e)))
            raise e
        self.metric_buffer[rounded_timestamp].append([x.cluster, x.version, x.weirdness_score])
        pass

    def _update_exposed_metrics(self):
        if self.metric_buffer:
            earliest_timestamp = min(self.metric_buffer)
            for metric_values in self.metric_buffer[earliest_timestamp]:
                self.weirdness_score_gauge.labels(cluster=str(metric_values[0]), version=str(metric_values[1])).set(metric_values[2])

                if [str(metric_values[0]),str(metric_values[1])] not in self.prev_metric_list:
                    self.prev_metric_list.append([str(metric_values[0]),str(metric_values[1])])
                pass
            del(self.metric_buffer[earliest_timestamp])

            if self.metric_buffer:
                self.update_interval = min(self.metric_buffer) - earliest_timestamp
                pass
        else:
            _LOGGER.debug("Metric buffer empty")
        pass

    def _delete_prev_metrics(self):
        while self.prev_metric_list:
            metric_label = self.prev_metric_list.pop()
            self.weirdness_score_gauge.remove(metric_label[0], metric_label[1])

    def start_server(self):
        # Start http server to expose metrics
        start_http_server(8000)
        while True:
            # delete existing exposed metrics
            self._delete_prev_metrics()

            # update exposed metric value
            self._update_exposed_metrics()

            _LOGGER.debug("Next metric update will be in {} seconds".format(self.update_interval))
            sleep(self.update_interval)
            pass
        pass
