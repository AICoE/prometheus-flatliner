from .baseflatliner import BaseFlatliner
from statistics import stdev


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

        # grab the resource name and the cluster id
        resource = self.metric_label(x, 'resource')
        cluster_id = self.cluster_id(x)
        version_id = self.metric_label(x,"gitVersion")

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
    def calculate_stdv(values, name, cluster, version, previous = None):
        num_entires = len(values)
        if previous:
            for x in values:
                current_value = int(x[1])
                current_count = previous['count'] + 1
                current_total = previous['total'] + current_value
                current_mean = current_total / current_count

                m2 = previous['m2'] + (current_value - previous['mean'])*(current_value-current_mean)
                std_dev = (m2/(current_count-1))**0.5

                previous['count'] = current_count
                previous['total'] = current_total
                previous['mean'] = current_mean
                previous['m2'] = m2
                previous['std_dev'] = std_dev

            count = current_count
            mean = current_mean
            total = current_total



        else:
            # intilize values if there is not previous data.
            count = num_entires
            if num_entires > 1:
                std_dev = stdev(int(x[1]) for x in values)
                total = sum(int(x[1]) for x in values)
                mean = total/num_entires
                m2 = sum(((int(x[1])-mean)**2) for x in values)

            else:
                std_dev = 0
                total = int(values[0][1])
                mean = int(values[0][1])
                m2 = 0

        return {'cluster': cluster, 'resource': name, 'std_dev': std_dev, 'm2': m2, 'mean': mean,
                'total': total, 'count': count, 'version': version}


