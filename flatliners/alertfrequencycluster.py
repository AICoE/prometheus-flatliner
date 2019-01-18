import time
from datetime import datetime
from dataclasses import dataclass

from .baseflatliner import BaseFlatliner

class AlertFrequencyCluster(BaseFlatliner):

    """
    This class contains the code for correlation of alerts for every cluster

    """

    def __init__(self):
        super().__init__()
        # Hold the values for different clusters
        self.clusters = dict()

    def on_next(self, x):
        """ On each entry we will update the frequency of alerts for a 30 minute time window
        """

        if not self.metric_name(x) == 'alerts':
            return

        alert_name = self.metric_label(x, 'alertname')
        cluster_id = self.cluster_id(x)
        time_stamp = self.metric_values(x)[0][0]
        time_window = 30  # in minutes

        if cluster_id not in self.clusters:
             self.clusters[cluster_id] = dict()

        if alert_name not in self.clusters[cluster_id]:
            self.intilize_freqency(x, alert_name,cluster_id)

        else:
            self.calculate_frequency(alert_name,cluster_id, time_window, time_stamp)

        self.publish(self.clusters[cluster_id][alert_name])


    def intilize_freqency(self, x, alert_name, cluster_id):

        state = self.State()
        state.cluster = self.cluster_id(x)
        state.alert = self.metric_label(x,'alertname')
        state.version = self.cluster_version(x)
        state.frequency = 1.0
        state.timestamp = self.metric_values(x)[0][0]
        state.time_stamps = [self.metric_values(x)[0][0]]

        self.clusters[cluster_id][alert_name] = state

    def calculate_frequency(self, alert_name,cluster_id, time_window, time_stamp):

        time_limit = time_window * 60
        self.clusters[cluster_id][alert_name].timestamp = time_stamp
        self.clusters[cluster_id][alert_name].time_stamps =  [x for x in self.clusters[cluster_id][alert_name].time_stamps
                                    if x >= (time_stamp-time_limit)]

        self.clusters[cluster_id][alert_name].time_stamps.append(time_stamp)

        # using the length of the timestamps should suffice to determine the frequency as the value is always 1
        self.clusters[cluster_id][alert_name].frequency = float(len(self.clusters[cluster_id]
                                                             [alert_name].time_stamps))


    @dataclass
    class State:

        cluster: str = ""
        alert: str = ""
        version: str = ""
        frequency: float = 0.0
        timestamp: float = 0.0
        time_stamps: str = ""