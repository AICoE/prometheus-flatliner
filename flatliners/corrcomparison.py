from .baseflatliner import BaseFlatliner

import numpy as np
import pandas

class CorrComparisonScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()
        self.clusters = dict()
        self.versions = dict()

    def on_next(self, x):
        """ update l2 distance between cluster vector and baseline vector
        """
        # determine entry type
        entry_type = 'unkown'
        
        if isinstance(x[list(x.keys())[0]], pandas.core.frame.DataFrame):
            entry_type = 'version'

        if isinstance(x[list(x.keys())[0]], dict):
            entry_type = 'cluster'

        # update the dataframes for each entry type
        if entry_type == 'version':
            self.versions = x

        if entry_type == 'cluster':
            self.clusters = x
            # Calculate/update the distances for each available cluster
            for cluster_name in self.clusters.keys():
                cluster_version = self.clusters[cluster_name]['version']
                # confirm version records have data for current cluster version
                if cluster_version in self.versions.keys():
                    # get vectors and remove NaN's
                    version_data, cluster_data = self.preprocess_data(cluster_name)
                    # confirm version and cluster vectors match
                    if version_data.shape == cluster_data.shape:
                        # calculate distance
                        self.compute_cluster_distance(version_data, cluster_data, cluster_name)

                        self.publish(self.score[cluster_name])


    def compute_cluster_distance(self, version_data, cluster_data, cluster_name):
        combine = np.subtract(version_data, cluster_data)
        norm = np.sqrt(np.square(combine).sum(axis=1))
        self.score[cluster_name] = {'cluster': cluster_name, 'corr_norm': norm.values[0]}

    def preprocess_data(self,cluster_name):
        cluster_version = self.clusters[cluster_name]['version']
        cluster_data = self.clusters[cluster_name]['dataframe']
        version_data = self.versions[cluster_version].tail(1)
        version_data = version_data.drop(version_data.columns[0], axis=1)
        version_data = version_data.fillna(0)
        cluster_data = cluster_data.fillna(0)

        return version_data, cluster_data
