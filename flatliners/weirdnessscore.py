from .baseflatliner import BaseFlatliner

class WeirdnessScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()
        self.clusters = dict()
        self.versions = dict()

    def on_next(self, x):

        cluster_name = x['cluster']
        #self.publish(x)

        if cluster_name not in self.score:
            self.score[cluster_name] = dict()
            self.score[cluster_name]['cluster'] = cluster_name

        if list(x.keys())[1] == 'corr_norm':
            self.score[cluster_name]['corr'] = x['corr_norm']



        if list(x.keys())[1] == 'std_norm':
            self.score[cluster_name]['std_dev'] = x['std_norm']


        if len(list(self.score[cluster_name].keys()))>=3:
            self.score[cluster_name]['sum'] = self.score[cluster_name]['corr'] \
                                            + self.score[cluster_name]['std_dev']

            self.publish(self.score[cluster_name])
