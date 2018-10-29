from .baseflatliner import BaseFlatliner


class VersionedMetrics(BaseFlatliner):
    def __init__(self):
        print(" Inside versionedmetrics")
        super().__init__()

        # dict for versions that we already know
        self.cluster_versions = dict()

        # buffer for metrics whose versions are unknown
        self.buffer = dict()

    def on_next(self, x):
        if self.metric_name(x) == 'openshift_build_info':
            self.update_cluster_versions(x)
            return

        cluster_id = self.cluster_id(x)

        if cluster_id in self.cluster_versions:
            # publish metric if we already know the version
            version = self.cluster_versions[cluster_id]
            self.add_version_and_publish(x, version)
        else:
            # buffer metric if we haven't seen the version
            if cluster_id not in self.buffer:
                self.buffer[cluster_id] = []
            self.buffer[cluster_id].append(x)

    def update_cluster_versions(self, x):
        cluster_id = self.cluster_id(x)
        version = self.metric_label(x, 'gitVersion')
        # TODO: make sure this is actually the latest timestamp
        # timestamp = self.metric_values(x)[-1][0]
        # let's just assume it's a newer timestamp
        # We could also store the timestamp and the version
        # self.cluster_versions[cluster_id] = (timestamp, version)
        # but start simple
        self.cluster_versions[cluster_id] = version

        # flush buffered entries now that we know the version
        if cluster_id in self.buffer:
            for metric in self.buffer[cluster_id]:
                self.add_version_and_publish(metric, version)

            del self.buffer[cluster_id]

    def add_version_and_publish(self, metric, version):
        metric['metric']['gitVersion'] = version
        self.publish(metric)
