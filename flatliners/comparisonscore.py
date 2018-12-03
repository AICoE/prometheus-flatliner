from .baseflatliner import BaseFlatliner


class ComparisonScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()
        self.clusters = dict()
        self.versions = dict()


    def on_next(self, x):
        """ update l2 distance between cluster vector and baseline vector
        """
        # determine if entry is a version metric or if it is a cluster metric
        is_version_record = list(x.keys())[0] == 'version'
        is_cluster_record = list(x.keys())[0] == 'cluster'

        # for version records, collect the average standard deviation value for
        # each resource
        if is_version_record:
            self.set_version_std(x)

        if is_cluster_record:
            cluster_id = x['cluster']
            self.compute_cluster_distance(x)
            if self.ready_to_publish(x):
                self.publish(self.score[cluster_id])


    def set_version_std(self, values):
        # select necessary values
        resource = values['resource']
        version_id = values['version']
        # add field for version_id if needed
        if version_id not in self.versions:
            self.versions[version_id] = dict()
        # set the value for the version_id and resource from the version record
        self.versions[version_id][resource] = values['avg_std_dev']

    def compute_cluster_distance(self, values):
        # select necessary values
        cluster_id = values['cluster']
        value = values['std_dev']
        resource = values['resource']
        version_id = values['version']
        # add field for cluster_id if needed
        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = dict()

        # for cluster records take the squared difference between the current std_dev value and the version value
        # and then take the square root of the sum to calculate the Euclidean distance between vectors.
        # store final, single value for each cluster in scores.
        self.clusters[cluster_id][resource] = (value - self.versions[version_id][resource])**2
        self.score[cluster_id] = {'cluster': cluster_id, 'std_norm': (sum(list(self.clusters[cluster_id].values())))**0.5,
                                  "timestamp": values["timestamp"]}


    def ready_to_publish(self, x):
          cluster_id = x['cluster']
          resoure_name = x['resource']
        
          if resoure_name in self.clusters[cluster_id].keys():
              return True
          else:
              return False

