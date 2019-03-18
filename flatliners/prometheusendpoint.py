from time import sleep, time
from collections import defaultdict
from .baseflatliner import BaseFlatliner

# Prometheus client metric type and server imports
from prometheus_client import Gauge, start_http_server

# Set up logging
import logging
_LOGGER = logging.getLogger(__name__)

class PrometheusEndpoint(BaseFlatliner):
    def __init__(self, pruning_interval: int = 300):
        super().__init__()
        self.pruning_interval = pruning_interval

        _LOGGER.info("Prometheus Endpoint initialized. Metric pruning interval is {0} seconds".format(self.pruning_interval))

        self.published_metric_timestamps = defaultdict(list)
        # This is the gauge metric where the metric data is published
        self.weirdness_score_gauge = Gauge('weirdness_score','Weirdness score for the given Cluster and Version',['cluster','version'])

    def on_next(self, x):
        try:
            # update the published metrics
            self.weirdness_score_gauge.labels(cluster=str(x.cluster), version=str(x.version)).set(x.weirdness_score)

            # Store timestamp when the metric was published and metric version info
            self.published_metric_timestamps[str(x.cluster)] = [int(time()),str(x.version)]
        except Exception as e:
            _LOGGER.error("Couldn't process the following packet {0}. Reason: {1}".format(x, str(e)))
            raise e

    def _delete_stale_metrics(self):
        '''
        This function will remove any metric that was published $(pruning_interval) seconds ago or older
        '''
        timestamp_threshold = int(time()) - self.pruning_interval

        for cluster_id in list(self.published_metric_timestamps):
            if self.published_metric_timestamps[cluster_id][0] < timestamp_threshold:
                # if metric is stale, stop publishing it
                self.weirdness_score_gauge.remove(cluster_id, self.published_metric_timestamps[cluster_id][1])
                del self.published_metric_timestamps[cluster_id]


    def start_server(self):
        # Start http server to expose metrics
        http_server_port = 8000
        start_http_server(http_server_port)
        _LOGGER.info("http server started on port {0}".format(http_server_port))
        while True:
            # delete stale exposed metrics
            self._delete_stale_metrics()

            _LOGGER.debug("Next metric pruning will be in {} seconds".format(self.pruning_interval))
            sleep(self.pruning_interval)
