from dataclasses import dataclass

from .baseflatliner import BaseFlatliner

class AlertFrequencyCluster(BaseFlatliner):

    """
    This class contains the code for correlation of alerts for every cluster

    """

    def __init__(self):
        super().__init__()
        # Hold the values for different clusters
        # For maxsize, it should be bigger than the number of new cluster ids coming
        # in during the time window (30 mins)
        # promql: count(sum(count_over_time(cluster_version[30m])) by (_id))
        self.clusters = self.create_cache_dict(maxsize=1000)

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

        self.normalize_cluster(cluster_id, alert_name)
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


    def normalize_cluster(self, cluster_id, alert):
        # get the values:
        alert_names = list(self.clusters[cluster_id].keys())
        alert_vector_length = len(alert_names)
        alert_list = []

        if alert_vector_length == 1:
            self.clusters[cluster_id][alert].frequency = 1.0
            return

        for i in alert_names:
            alert_list.append(self.clusters[cluster_id][i].frequency)
        max_value = max(alert_list)
        min_value = min(alert_list)

        for value, name in zip(alert_list, alert_names):
            if max_value != min_value:
                self.clusters[cluster_id][name].frequency = ((value - min_value)/(max_value - min_value))\
                                                          / (alert_vector_length)**(0.5)
            else:
                self.clusters[cluster_id][name].frequency = 1.0


    @dataclass
    class State:

        cluster: str = ""
        alert: str = ""
        version: str = ""
        frequency: float = 0.0
        timestamp: float = 0.0
        time_stamps: str = ""
