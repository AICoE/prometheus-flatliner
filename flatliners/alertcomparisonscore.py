from .baseflatliner import BaseFlatliner

from numpy.linalg import norm
from numpy import array
from dataclasses import dataclass
import flatliners

class AlertComparisonScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        # this dict stores the score for each cluster, so it should
        # be big enough to accomodate recent clusters coming in
        # promql: count (count (alerts) by (_id))
        # example:
        # {fbc1adc6-6ff0-4afc-affe-ff0594d6c7d8: {cluster='fbc1adc6-6ff0-4afc-affe-ff0594d6c7d8',
        #                                         version='4.0.0-0.1',
        #                                         alert='CPUThrottlingHigh',
        #                                         comparison_score=0.0,
        #                                         timestamp=1554217799.252,
        #                                         alert_deltas={'CPUThrottlingHigh': 0.0,
        #                                                       'CoreDNSDown': 0.0,
        #                                                       'DeadMansSwitch': 0.0,
        #                                                       'KubeAPIErrorsHigh': 0.0,
        #                                                       'KubeClientErrors': 0.0,
        #                                                       'KubeControllerManagerDown': 0.0,
        #                                                       'KubeSchedulerDown': 0.0})}
        self.score = self.create_cache_dict(maxsize=1000)

        # this dict stores alerts for each cluster, so it should
        # be big enough to accomodate recent clusters coming in
        # promql: count (count (alerts) by (_id))
        # example:
        # {fbc1adc6-6ff0-4afc-affe-ff0594d6c7d8: {'CPUThrottlingHigh': 1.0,
        #                                         'CoreDNSDown': 1.0,
        #                                         'DeadMansSwitch': 1.0,
        #                                         'KubeAPIErrorsHigh': 0.5,
        #                                         'KubeClientErrors': 0.4472135954999579,
        #                                         'KubeControllerManagerDown': 0.4082482904638631,
        #                                         'KubeSchedulerDown': 0.3779644730092272,
        #                                         'KubeVersionMismatch': 0.35355339059327373}
        self.clusters = self.create_cache_dict(maxsize=1000)

        # this dict stores alerts for each version, so it should
        # be big enough to accomodate recent versions coming in
        # promql: count (count (cluster_version) by (version))
        # example:
        # {4.0.0-0.7: {'KubeClientCertificateExpiration': 0.9948453608247423,
        #              'TargetDown': 0.9499880635026346,
        #              'Watchdog': 0.965060952797281,
        #              'OCS_CephPgStuck': 1.0,
        #              'KubeJobFailed': 1.0,
        #              'KubeClientErrors': 0.9511844635310913,
        #              'ClusterMonitoringOperatorErrors': 1.0,
        #              'KubeAPIErrorsHigh': 0.7071067811865475,
        #              'KubeAPILatencyHigh': 0.5773502691896258,
        #              'KubeDaemonSetMisScheduled': 0.4472135954999579,
        #              'KubeDaemonSetRolloutStuck': 0.4082482904638631,
        #              'KubeNodeNotReady': 0.3779644730092272,
        #              'KubePodNotReady': 0.7845177968644247,
        #              'KubeStatefulSetReplicasMismatch': 0.3333333333333333,
        #              'KubeDeploymentReplicasMismatch': 1.0,
        #              'KubeMemOvercommit': 1.0}
        self.versions = self.create_cache_dict(maxsize=200)

        # this dict stores alert deltas for each cluster, so it should
        # be big enough to accomodate recent clusters coming in
        # promql: count (count (alerts) by (_id))
        # example:
        # {ff2c773b-a2de-43b6-a501-36274cc8a1a5: {'KubeClientCertificateExpiration': 0.008346244408562575,
        #                                         'TargetDown': 0.060063351955155886,
        #                                         'Watchdog': 0.040937763985934184}
        self.alert_deltas = self.create_cache_dict(maxsize=1000)

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
        self.clusters[x.cluster][x.alert] = x.frequency

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
