from .baseflatliner import BaseFlatliner
from dataclasses import dataclass

from cachetools import LRUCache

class AlertFrequencyVersion(BaseFlatliner):

    """
    This class contains the functionalities to calculate
    alert correlation shift over multiple gitversion
    """

    def __init__(self, max_cache_size: int = 500):
        super().__init__()

        # holds the state objects for each version and alert
        self.version_frequencies = LRUCache(maxsize=max_cache_size)

    def on_next(self, x):
        """ On each data loading it will calculate the average alert frequency for an alert
        """

        alert = x.alert
        version = x.version

        if version not in self.version_frequencies:
            self.version_frequencies[version] = dict()

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
        state.cluster_frequencies = {x.cluster : x.frequency}
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
        self.version_frequencies[x.version][x.alert] = previous



    @dataclass
    class State:

        alert: str = ""
        version: str = ""
        cluster_frequencies: str = "" # becomes dictionary
        avg_frequency: float = 0.0
        timestamp: float = 0.0
