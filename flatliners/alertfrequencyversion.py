from .baseflatliner import BaseFlatliner
from dataclasses import dataclass

class AlertFrequencyVersion(BaseFlatliner):

    """
    This class contains the functionalities to calculate
    alert correlation shift over multiple gitversion
    """

    def __init__(self):
        super().__init__()

        # holds the state objects for each version and alert
        # maxsize should be at least equal to the number of unique versions
        # promql: count (count (cluster_version) by (version)) ,so maxsize = 200
        self.version_frequencies = self.create_cache_dict(maxsize=200)

    def on_next(self, x):
        """ On each data loading it will calculate the average alert frequency for an alert
        """

        alert = x.alert
        version = x.version

        if version not in self.version_frequencies:
            # this dict should be big enough to accomodate any recent alerts
            # promql: count(count(alerts) by (alertname))
            self.version_frequencies[version] = self.create_cache_dict(maxsize=100)

        if alert not in  self.version_frequencies[version]:
            self.initilize_version_alert(x)

        else:
            previous = self.version_frequencies[version][alert]
            self.update_version_alert(x, previous)

        self.publish(self.version_frequencies[version][alert])



    def initilize_version_alert(self, x):

        state = self.State()
        state.alert = x.alert
        state.version = x.version
        # The size of this dict should be able to accomodate the different cluster ids
        # coming in from the alerts metric
        # promql: count(count(alerts) by (_id))
        state.cluster_frequencies = self.create_cache_dict(maxsize=1000)
        state.cluster_frequencies[x.cluster] = x.frequency
        state.avg_frequency = x.frequency
        state.timestamp = x.timestamp
        self.version_frequencies[x.version][x.alert] = state


    def update_version_alert(self, x, previous):

        # update cluster frequency
        previous.cluster_frequencies[x.cluster] = x.frequency
        # compute average frequency
        previous_values = list(previous.cluster_frequencies.values())
        previous.avg_frequency = sum(previous_values) / float(len(previous_values))
        # update time_stamp
        previous.timestamp = x.timestamp
        # reset entry
        self.version_frequencies[x.version][x.alert] =  previous



    @dataclass
    class State:

        alert: str = ""
        version: str = ""
        cluster_frequencies: str = "" # becomes dictionary
        avg_frequency: float = 0.0
        timestamp: float = 0.0