from .baseflatliner import BaseFlatliner



class DfGenerator(BaseFlatliner):
    def __init__(self):
        print(" Inside alert corr")
        super().__init__()
        self.clusters = dict()

    def on_next(self, x):
        """ update calculate std dev for cluster
        """
        # print(f"got {x}")

        if not self.metric_name(x) == 'alerts':
            return

        alert_name = self.metric_label(x, 'alertname')
        cluster_id = self.cluster_id(x)

        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = dict()

        if alert_name not in self.clusters[cluster_id]:
            self.clusters[cluster_id][alert_name] = self.metric_values(x)

        else:
            previous = self.clusters[cluster_id][alert_name]
            previous.extend(self.metric_values(x))
            self.clusters[cluster_id][alert_name] = previous
        #self.clusters[cluster_id] =
        self.print_values(self.clusters[cluster_id])

        self.publish(self.clusters[cluster_id])

    def on_completed(self):
        #print(self.clusters)
        print("Done!")

    @staticmethod
    def print_values(clusters):
        return clusters
