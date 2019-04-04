from .baseflatliner import BaseFlatliner
from statistics import stdev
from dataclasses import dataclass

class StdDevCluster(BaseFlatliner):
    def __init__(self):
        super().__init__()

        # this dict needs to store a StdDevCluster.State object  for every resource
        # in a cluster
        # promql: count (count (etcd_object_counts) by (_id))
        # {022b5bf4-c124-41b7-9be6-db24079e45ce:
        #        {'alertmanagers.monitoring.coreos.com': (cluster='022b5bf4-c124-41b7-9be6-db24079e45ce',
        #                                                 resource='alertmanagers.monitoring.coreos.com',
        #                                                 std_dev=0.0,
        #                                                 m2=0.0,
        #                                                 mean=0.5,
        #                                                 total=0.0,
        #                                                 count=2,
        #                                                 version='4.0.0-0.9',
        #                                                 timestamp=1554390815.484) ................
        self.clusters = self.create_cache_dict(maxsize=1000)

    def on_next(self, x):
        """ update calculate std dev for cluster
        """
        # stop if the metric name is not etcd_object_count
        if not self.metric_name(x) == 'etcd_object_counts':
            return

        # grab the resource name and the cluster id
        resource = self.metric_label(x, 'resource')
        cluster_id = self.cluster_id(x)
        version_id = self.cluster_version(x)

        # if cluster_id is not present add it as an empty dictionary
        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = dict()

        # if the resource hasen't been seen before, do std_dev initilization
        if resource not in self.clusters[cluster_id]:
            self.clusters[cluster_id][resource] = self.calculate_stdv(self.metric_values(x), resource,
                                                                      cluster_id, version_id)

        # if the resource exists, grab the last entry for that cluster.
        # set the new value to the updated values.
        else:
            previous = self.clusters[cluster_id][resource]
            self.clusters[cluster_id][resource] = self.calculate_stdv(self.metric_values(x), resource,
                                                                      cluster_id, version_id, previous)

        self.normalize_cluster(cluster_id, resource)
        self.clusters[cluster_id][resource].timestamp = x["values"][0][0]
        self.publish(self.clusters[cluster_id][resource])


    @staticmethod
    def continue_calculation(values, previous):
        for x in values:
            current_value = int(x[1])
            current_count = previous.count + 1
            current_total = previous.total + current_value
            current_mean = current_total / current_count

            m2 = previous.m2 + abs((current_value - previous.mean) * (current_value - current_mean))
            # added absolute value function to prevent std from being expressed as an imaginary number.
            std_dev = (m2 / (current_count - 1)) ** 0.5

            previous.count = current_count
            previous.total = current_total
            previous.mean = current_mean
            previous.m2 = m2
            previous.std_dev = std_dev

        count = current_count
        mean = current_mean
        total = current_total

        return count, mean, total, std_dev, m2



    @staticmethod
    def initilize_calculation(values):
        # intilize values if there is not previous data.
        num_entires = len(values)
        count = num_entires

        if num_entires > 1:
            std_dev = stdev(int(x[1]) for x in values)
            total = sum(int(x[1]) for x in values)
            mean = total / num_entires
            m2 = sum(((int(x[1]) - mean) ** 2) for x in values)

        else:
            std_dev = 0
            total = int(values[0][1])
            mean = int(values[0][1])
            m2 = 0

        return count, mean,total, std_dev, m2


    def calculate_stdv(self, values, name, cluster, version, previous = None):
        if previous:
            count, mean, total, std_dev, m2 = self.continue_calculation(values, previous)
        else:
            count, mean, total, std_dev, m2 = self.initilize_calculation(values)

        state = self.State()
        state.cluster = cluster
        state.resource = name
        state.std_dev = std_dev
        state.m2 = m2
        state.mean = mean
        state.count = count
        state.version = version

        return state


    def normalize_cluster(self, cluster_id, resource):
        # get the values:
        resource_names = list(self.clusters[cluster_id].keys())
        resource_vector_length = len(resource_names)
        resource_list = []

        if resource_vector_length == 1:
            self.clusters[cluster_id][resource].std_dev = 0.0
            return

        for i in resource_names:
            resource_list.append(self.clusters[cluster_id][i].std_dev)
        max_value = max(resource_list)
        min_value = min(resource_list)

        for value, name in zip(resource_list, resource_names):
            if max_value != min_value:
                self.clusters[cluster_id][name].std_dev = ((value - min_value)/(max_value - min_value))\
                                                          / (resource_vector_length)**(0.5)
            else:
                self.clusters[cluster_id][name].std_dev = 0.0


    @dataclass
    class State:

        cluster: str = ""
        resource: str = ""
        std_dev: float = 0.0
        m2: float = 0.0
        mean: float = 0.0
        total: float = 0.0
        count: float = 0.0
        version: str = ""
        timestamp: float = 0.0



