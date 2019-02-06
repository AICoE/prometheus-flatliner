from .baseflatliner import BaseFlatliner
import flatliners
from dataclasses import dataclass

class ResourceComparisonScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()
        self.clusters = dict()
        self.versions = dict()
        self.resource_deltas = dict()


    def on_next(self, x):
        """ update l2 distance between cluster vector and baseline vector
        """
        # for version records, collect the average standard deviation value for
        # each resource
        if isinstance(x, flatliners.stddevversion.StdDevVersion.State):
            self.set_version_std(x)

        if isinstance(x, flatliners.stddevcluster.StdDevCluster.State):
            cluster_id = x.cluster
            self.compute_cluster_distance(x)
            if self.ready_to_publish(x):
                self.publish(self.score[cluster_id])


    def set_version_std(self, values):
        # select necessary values
        resource = values.resource
        version_id = values.version
        # add field for version_id if needed
        if version_id not in self.versions:
            self.versions[version_id] = dict()
        # set the value for the version_id and resource from the version record
        self.versions[version_id][resource] = values.avg_std_dev

    def compute_cluster_distance(self, values):
        # select necessary values
        cluster_id = values.cluster
        value = values.std_dev
        resource = values.resource
        version_id = values.version
        # add field for cluster_id if needed
        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = dict()

        # for cluster records take the squared difference between the current std_dev value and the version value
        # and then take the square root of the sum to calculate the Euclidean distance between vectors.
        # store final, single value for each cluster in scores.
        self.clusters[cluster_id][resource] = (value - self.versions[version_id][resource])**2

        if cluster_id not in self.resource_deltas:
            self.resource_deltas[cluster_id] = dict()
        self.resource_deltas[cluster_id][resource] = abs(self.clusters[cluster_id][resource]-
                             self.versions[version_id][resource])

        state = self.State()
        state.cluster = cluster_id
        state.version = values.version
        state.resource = values.resource
        state.std_norm = (sum(list(self.clusters[cluster_id].values())))**0.5
        state.timestamp = values.timestamp
        state.resource_deltas = self.resource_deltas[cluster_id]

        self.score[cluster_id] = state

    def ready_to_publish(self, x):
          cluster_id = x.cluster
          resoure_name = x.resource
        
          if resoure_name in self.clusters[cluster_id].keys():
              return True
          else:
              return False

    @dataclass
    class State:

        cluster: str = ""
        version: str = ""
        resource: str = ""
        std_norm: float = 0.0
        timestamp:float = 0.0
        resource_deltas: str = ""