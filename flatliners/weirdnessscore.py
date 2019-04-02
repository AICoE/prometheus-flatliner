from .baseflatliner import BaseFlatliner
import flatliners

from dataclasses import dataclass

class WeirdnessScore(BaseFlatliner):
    def __init__(self):
        super().__init__()
        # this dict needs to store the resource state for each cluster
        # promql: count (count (etcd_object_counts) by (_id))
        # example:
        # 4f3fa2db-bcc7-4a70-bc53-2501ebbf235a: {cluster='4f3fa2db-bcc7-4a70-bc53-2501ebbf235a',
        #                                        version='4.0.0-0.7',
        #                                        resource='roles.rbac.authorization.k8s.io',
        #                                        std_dev=0.12843759382881617,
        #                                        timestamp=1554219689.252,
        #                                        weirdness_score=0.12750775288668642,
        #                                        std_dev_buffer=True,
        #                                        resource_deltas={'alertmanagers.monitoring.coreos.com': 0.001620557938884463,
        #                                                         'apiservices.apiregistration.k8s.io': 0.03206530312721848
        #                                                         ..................}
        self.resource_score = self.create_cache_dict(maxsize=1000)

        # this dict needs to store the alert state for each cluster
        # promql: count (count (etcd_object_counts) by (_id))
        # fd6383f1-414c-4361-8a3e-e7eaed578eed {cluster='fd6383f1-414c-4361-8a3e-e7eaed578eed',
        #                                       version='4.0.0-0.7',
        #                                       alert='KubeClientCertificateExpiration',
        #                                       weirdness_score=0.0853890113837755,
        #                                       timestamp=1554219956.683,
        #                                       alert_deltas={'KubeClientCertificateExpiration': 0.008346244408562575,
        #                                                     'Watchdog': 0.08498013573401186})
        self.alert_score = self.create_cache_dict(maxsize=1000)

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
        weirdness_score:float = 0.0
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
