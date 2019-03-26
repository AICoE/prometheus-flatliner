from .baseflatliner import BaseFlatliner
import flatliners

from cachetools import LRUCache

from dataclasses import dataclass

class WeirdnessScore(BaseFlatliner):
    def __init__(self, max_cache_size: int = 500):
        super().__init__()

        self.resource_score = LRUCache(maxsize=max_cache_size)
        self.alert_score = LRUCache(maxsize=max_cache_size)

    def on_next(self, x):

        cluster_name = x.cluster
        version = x.version

        if isinstance(x, flatliners.resourcecomparisonscore.ResourceComparisonScore.State):

            if cluster_name not in self.resource_score:
                self.resource_score[cluster_name] = self.Resource_State()
                self.resource_score[cluster_name].cluster = cluster_name

            self.resource_score[cluster_name].std_dev = float(x.std_norm)
            self.resource_score[cluster_name].timestamp = float(x.timestamp)
            self.resource_score[cluster_name].std_dev_buffer = True
            self.resource_score[cluster_name].version = version
            self.resource_score[cluster_name].resource = x.resource
            self.resource_score[cluster_name].resource_deltas = x.resource_deltas

            if self.resource_score[cluster_name].std_dev_buffer:
                self.resource_score[cluster_name].weirdness_score = self.resource_score[cluster_name].std_dev
                self.publish(self.resource_score[cluster_name])

        if isinstance(x, flatliners.alertcomparisonscore.AlertComparisonScore.State):
            if cluster_name not in self.alert_score:
                self.alert_score[cluster_name] = self.Alert_Sate()
                self.alert_score[cluster_name].cluster = cluster_name

            self.alert_score[cluster_name].version = x.version
            self.alert_score[cluster_name].alert = x.alert
            self.alert_score[cluster_name].weirdness_score = x.comparison_score
            self.alert_score[cluster_name].timestamp = float(x.timestamp)
            self.alert_score[cluster_name].alert_deltas = x.alert_deltas

            self.publish(self.alert_score[cluster_name])



    @dataclass
    class Resource_State:

        cluster: str = ""
        version: str = ""
        resource: str = ""
        std_dev: float = 0.0
        timestamp: float = 0.0
        weirdness_score: float = 0.0
        std_dev_buffer: bool = False
        resource_deltas: str = ""

    @dataclass
    class Alert_Sate:
        cluster: str = ""
        version: str = ""
        alert: str = ""
        weirdness_score: float = 0.0
        timestamp: float = 0.0
        alert_deltas: str = ""
