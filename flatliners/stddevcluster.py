from .baseflatliner import BaseFlatliner


class StdDevCluster(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.clusters = dict()

    def on_next(self, x):
        """ update calculate std dev for cluster
        """
        # stop if the metric name is not etcd_object_count
        if not self.metric_name(x) == 'etcd_object_counts':
            return

        resource = self.metric_label(x, 'resource')
        cluster_id = self.cluster_id(x)

        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = dict()

        if resource not in self.clusters[cluster_id]:
            #self.clusters[cluster_id][resource] = self.calculate_mean(self.metric_values(x))
            self.clusters[cluster_id][resource] = self.calculate_stdv(self.metric_values(x))
        else:
            previous = self.clusters[cluster_id][resource]
            #self.clusters[cluster_id][resource] = self.calculate_mean(self.metric_values(x), previous)
            self.clusters[cluster_id][resource] = self.calculate_stdv(self.metric_values(x), previous)

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

    @staticmethod
    def calculate_stdv(values, previous = None):
        if previous:

            total = previous['total'] + int(values[0][0]) # I'm not 100% sure if this is the correct way to organize the data.
            mean = total / len(values)
            m2 = previous['m2'] + (int(values[0][0]) - previous['mean'])*(int(values[0][0]) - mean)
            std_dev = (m2/(len(values)))**(0.5)


        else:
            # intilize values if there is not previous data.
            std_dev = 0
            m2 = 0
            mean = int(values[0][0])
            total = sum(int(x[1]) for x in values)


        return {'std_dev': std_dev, 'm2' : m2, 'mean' : mean, 'total' : total}


