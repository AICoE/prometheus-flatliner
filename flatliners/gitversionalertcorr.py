import math
import pandas as pd
import numpy as np
from datetime import datetime
from .baseflatliner import BaseFlatliner
from itertools import combinations

class GitVersionAlertCorrelation(BaseFlatliner):

    """
    This class contains the functionalities to calculate
    alert correlation shift over multiple gitversion
    """

    def __init__(self):
        super().__init__()
        # Holds the values for different gitVersions aka cluster versions
        self.gitVersions = dict()
        # Holds the values of correlation for every git version
        self.clusters_version_correlation = dict()
        # To keep track of previous publish
        self.timestamp = datetime.fromtimestamp(0)
        # Keep the set of unique alerts' combination
        self.unique_alert_combination =[]

    def on_next(self, x):
        """ On each data loading it will create dataframe and then pivot frame
        """
        # print(f"got {x}")

        if not self.metric_name(x) == 'alerts':
            return

        alert_name = self.metric_label(x, 'alertname')
        cluster_id = self.cluster_id(x)
        git_version = self.cluster_version(x)

        if git_version not in self.gitVersions:
            self.gitVersions[git_version] = pd.DataFrame(\
                columns=['_id', 'timestamp', 'alertname', 'gitVersion'])

        git_version_df = self.gitVersions[git_version]

        # Dataframe creation
        timestamps = []
        alerts = []

        for elem in self.metric_values(x):
            timestamps.append(datetime.fromtimestamp(elem[0]))
            alerts.append(alert_name)

        git_version_df = git_version_df.append(
            pd.DataFrame({'_id': [cluster_id] * len(timestamps), 'timestamp': timestamps,
                          'alertname': alerts, 'gitVersion': [git_version] * len(timestamps)}))

        git_version_df.reset_index(drop= True, inplace= True)

        self.gitVersions[git_version] = git_version_df

        # Publishing for every hour
        if(datetime.timestamp(timestamps[-1]) - datetime.timestamp(self.timestamp)) > 3600:

            self.timestamp = timestamps[-1]

            all_git_version_corr_shift = {}
            pivot_frame_dict = {}
            for unique_git in sorted(self.gitVersions.keys()):
                df_single_git_version_all_clusters_alert = self.gitVersions[unique_git]

                columns_required = ['alertname', 'timestamp']
                df_filtered = df_single_git_version_all_clusters_alert[columns_required]
                df_count_half_hour = pd.DataFrame()
                for alert_name in list(df_filtered['alertname'].unique()):
                    df_count_half_hour[alert_name] = ((df_filtered[df_filtered['alertname'] == alert_name]).groupby(
                        pd.Grouper(key='timestamp', freq='10min')).count())['alertname']
                df_count_half_hour['timestamp'] = df_count_half_hour.index.values
                pivot_frame_dict[unique_git] = df_count_half_hour

                try:
                    self.clusters_version_correlation[unique_git] = \
                        df_count_half_hour[df_count_half_hour.columns.difference(['timestamp'])].corr()
                except Exception:
                    self.clusters_version_correlation[unique_git] = None

            for unique_git in sorted(self.gitVersions.keys()):
                git_version_corr_shift = self.corr_change_over_build_and_time(unique_git, pivot_frame_dict)
                all_git_version_corr_shift[unique_git] = git_version_corr_shift
                columns = list(git_version_corr_shift.columns.difference(['timestamp']).values)

                for elem in columns:
                    if elem not in self.unique_alert_combination:
                        self.unique_alert_combination.append(elem)

                # self.unique_alert_comb.extend(columns)
                # self.unique_alert_comb = list(set(unique_alert_comb))
            # Publishing correlation shift of every git version
            self.publish(all_git_version_corr_shift)

    def alert_name(self, x):
        """
        Returns alert name of current stream
        :param x:
        :return:
        """
        return self.metric_label(x, 'alertname')

    def corr_change_over_build_and_time(self, git_version, pivot_frame_dict):
        """
        Calculate correlation change for a particular git version over time
        :param git_version:
        :param pivot_frame_dict: holds alert count of every type of alert for every git version
        :return:
        """

        low = 0
        timestamp_l = []
        pivot_group = pivot_frame_dict[git_version]
        if pivot_group is None:
            return None

        L = list(pivot_group.columns.difference(['timestamp']).values)
        element_dict = {'timestamp': []}
        for elm in list(combinations(L, 2)):
            element_dict['_'.join(elm)] = []

        for i in range(3, len(pivot_group) + 1, 1):
            timestamp = pivot_group[(low + 1): (i + 1)]['timestamp'].values[-1]
            correlation_matrix_last_five = pivot_group[low: i][pivot_group.columns.difference(['timestamp'])]
            correlation_matrix_with_current = pivot_group[(low + 1): (i + 1)][
                pivot_group.columns.difference(['timestamp'])]
            diff_corr = (correlation_matrix_last_five.corr() - correlation_matrix_with_current.corr()).dropna(
                axis=[0, 1], how='all')
            mask = np.zeros_like(diff_corr, dtype=np.bool)
            mask[np.triu_indices_from(mask)] = True
            diff_corr = diff_corr.mask(mask)
            element_dict['timestamp'].append(pivot_group['timestamp'][i - 1])
            for elm in list(combinations(L, 2)):
                try:
                    val = diff_corr.get_value(index=elm[1], col=elm[0])

                except KeyError:
                    val = math.nan
                element_dict['_'.join(elm)].append(val)
            low += 1
            timestamp_l.append(timestamp)

        return pd.DataFrame(element_dict)

    def get_single_cluster_version_corr(self, git_version):
        """
        Returns correlation of a particular git version
        :param git_version:
        :return:
        """
        return self.clusters_version_correlation[git_version]

    @staticmethod
    def print_values(dataframe_dict, timestamp):
        print("Printing for :", timestamp)
        for key in dataframe_dict.keys():
            print("Cluster_id:", key, " in timestamp:", timestamp)
            print(dataframe_dict[key])
        return None



    @staticmethod
    def print_git_frame(git_frame, git_version, ops='Value'):
        """

        :param git_frame:
        :param git_version:
        :param ops:
        :return:
        """
        print("Printing" + ops + " for :", git_version)
        print(git_frame.head())