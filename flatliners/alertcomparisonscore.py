from .baseflatliner import BaseFlatliner

from numpy.linalg import norm
from numpy import array
from dataclasses import dataclass
import flatliners

class AlertComparisonScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()
        self.clusters = dict()
        self.versions = dict()
        self.alert_deltas = dict()

    def on_next(self, x):
        """ update l2 distance between cluster vector and baseline vector
        """
        # determine entry type
        if isinstance(x, flatliners.alertfrequencyversion.AlertFrequencyVersion.State):
            # if we have version data, we want to populate/ update a version record
            self.update_version_alerts(x)

        if isinstance(x, flatliners.alertfrequencycluster.AlertFrequencyCluster.State):
            # if we have cluster_data we want to populate/ update a cluster record
            self.update_cluster_alerts(x)
            # and compare version and cluster values
            if x.cluster not in self.score:
                self.initialize_metric_state(x)

            self.score[x.cluster].comparison_score = self.compute_norm(x)
            self.score[x.cluster].timestamp = x.timestamp
            self.compute_alert_delta(x)
            if self.ready_to_publish(x):
                self.publish(self.score[x.cluster])


    def update_version_alerts(self,x):
        if x.version not in self.versions:
            self.versions[x.version]= dict()
        self.versions[x.version][x.alert] = x.avg_frequency

    def update_cluster_alerts(self,x):
        if x.cluster not in self.clusters:
            self.clusters[x.cluster] = dict()
        self.clusters[x.cluster][x.alert] = x.avg_frequency

    def initialize_metric_state(self,x):
        state = self.State()
        state.cluster = x.cluster
        state.version = x.version
        state.alert = x.alert
        state.comparison_score = 0
        state.timestamp = x.timestamp
        self.score[x.cluster] = state

    def compute_norm(self,x):
        # Build the subtracted value array by matching values by alert names as no guarantee dictionaries are in order
        subtracted_metrics = []
        # Loop on cluster keys to avoid matching alerts found in version but not in cluster
        # in some cases the cluster record is updated prior to the version, if/else circumvents this for now
        # TODO: ensure version records always updated prior to cluster record
        for alert in list(self.clusters[x.cluster].keys()):
            if alert not in self.versions[x.version]:
                pass
            else:
                subtracted_metrics.append(self.versions[x.version][alert]
                                          - self.clusters[x.cluster][alert])
        subtracted_metrics = array(subtracted_metrics)
        return norm(subtracted_metrics)

    def compute_alert_delta(self,x):
        delta = abs(self.versions[x.version][x.alert] - self.clusters[x.cluster][x.alert])
        if x.cluster not in self.alert_deltas:
            self.alert_deltas[x.cluster] = dict()
        self.alert_deltas[x.cluster][x.alert]  = delta
        self.score[x.cluster].alert_deltas = self.alert_deltas[x.cluster]

    def ready_to_publish(self, x):
        cluster_id = x.cluster
        alert = x.alert

        if alert in self.clusters[cluster_id].keys():
            return True
        else:
            return False


    @dataclass
    class State:
        cluster: str = ""
        version:str = ""
        alert:str = ""
        comparison_score: float = 0.0
        timestamp: float = 0.0
        alert_deltas:str =  ""