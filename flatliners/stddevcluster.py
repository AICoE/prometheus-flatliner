from .baseflatliner import BaseFlatliner


class StdDevCluster(BaseFlatliner):
    def __init__(self):
        print(" Inside stddevcluster")
        super().__init__()

        self.clusters = dict()

    def on_next(self, x):
        """ update calculate std dev for cluster
        """
        # print(f"got {x}")

        if not self.metric_name(x) == 'etcd_object_counts':
            return

        resource = self.metric_label(x, 'resource')
        cluster_id = self.cluster_id(x)

        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = dict()

        if resource not in self.clusters[cluster_id]:
            self.clusters[cluster_id][resource] = self.calculate_mean(self.metric_values(x))
        else:
            previous = self.clusters[cluster_id][resource]
            self.clusters[cluster_id][resource] = self.calculate_mean(self.metric_values(x), previous)

        self.publish(self.clusters[cluster_id][resource])

    @staticmethod
    def calculate_mean(values, previous = None):
        if previous:
            count = len(values) + previous['count']
            v_sum = previous['count'] * previous['mean']
        else:
            count = len(values)
            v_sum = 0

        v_sum += sum(int(x[1]) for x in values)
        return {'count': count, 'mean': v_sum / count}
