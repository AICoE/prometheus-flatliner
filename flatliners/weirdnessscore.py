from .baseflatliner import BaseFlatliner

class WeirdnessScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()
        self.clusters = dict()
        self.versions = dict()

    def on_next(self, x):

        cluster_name = x['cluster']

        if cluster_name not in self.score:
            self.score[cluster_name] = dict()
            self.score[cluster_name]['cluster'] = cluster_name

        if list(x.keys())[1] == 'corr_norm':
            self.score[cluster_name]['corr'] = float(x['corr_norm'])
            self.score[cluster_name]['timestamp_corr'] = float(x["timestamp"])


        if list(x.keys())[1] == 'std_norm':
            self.score[cluster_name]['std_dev'] = float(x['std_norm'])
            self.score[cluster_name]['timestamp_std'] = float(x['timestamp'])


        if len(list(self.score[cluster_name].keys()))>=5:
            self.score[cluster_name]['sum'] = self.score[cluster_name]['corr'] \
                                            + self.score[cluster_name]['std_dev']

            self.publish(self.score[cluster_name])
