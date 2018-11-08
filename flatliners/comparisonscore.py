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
            self.set_version_std(self.versions, x)

        if is_cluster_record:
            cluster_id = x['cluster']
            self.compute_cluster_distance(self.clusters, self.versions, x, self.score)
            if self.ready_to_publish(x):
                self.publish(self.score[cluster_id])

    @staticmethod
    def set_version_std(version_records, values):
        # select necessary values
        resource = values['resource']
        version_id = values['version']
        # add field for version_id if needed
        if version_id not in version_records:
            version_records[version_id] = dict()
        # set the value for the version_id and resource from the version record
        version_records[version_id][resource] = values['avg_std_dev']


    @staticmethod
    def compute_cluster_distance(cluster_records, version_records, values, scores):
        # select necessary values
        cluster_id = values['cluster']
        value = values['std_dev']
        resource = values['resource']
        version_id = values['version']
        # add field for cluster_id if needed
        if cluster_id not in cluster_records:
            cluster_records[cluster_id] = dict()

        # for cluster records take the squared difference between the current std_dev value and the version value
        # and then take the square root of the sum to calculate the Euclidean distance between vectors.
        # store final, single value for each cluster in scores.
        cluster_records[cluster_id][resource] = (value - version_records[version_id][resource])**2
        scores[cluster_id] = (sum(list(cluster_records[cluster_id].values())))**0.5

    def ready_to_publish(self, x):
        cluster_id = x['cluster']
        resoure_name = x['resource']

        if resoure_name in self.clusters[cluster_id].keys():
            return True
        else:
            return False
