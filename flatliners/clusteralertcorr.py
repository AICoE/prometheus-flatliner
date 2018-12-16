import math
import numpy as np
import pandas as pd
import time
from datetime import datetime
from itertools import combinations
from .baseflatliner import BaseFlatliner

class ClusterAlertCorrelation(BaseFlatliner):

    """
    This class contains the code for correlation of alerts for every cluster

    """

    def __init__(self):
        super().__init__()
        # Hold the values for different clusters
        self.clusters = dict()
        # Hold 1-D vector for every cluster id of alert to alert correlation
        self.clusters_correlation = dict()
        # To keep track of previous publish
        self.timestamp = datetime.fromtimestamp(0)

    def on_next(self, x):
        """ On each data loading it will create dataframe and then pivot frame
        """
        # print(f"got {x}")

        if not self.metric_name(x) == 'alerts':
            return

        alert_name = self.metric_label(x, 'alertname')
        cluster_id = self.cluster_id(x)
        version_id = self.cluster_version(x)

        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = pd.DataFrame(columns=['_id', 'timestamp', 'alertname'])
            self.clusters_correlation[cluster_id] = pd.DataFrame()

        cluster_df = self.clusters[cluster_id]

        # Dataframe creation
        timestamps = []
        alerts = []

        for elem in self.metric_values(x):
            timestamps.append(datetime.fromtimestamp(elem[0]))
            alerts.append(alert_name)

        cluster_df = cluster_df.append(\
            pd.DataFrame({'_id': [cluster_id] * len(timestamps), 'timestamp': timestamps, 'alertname': alerts}))

        cluster_df.reset_index(drop= True, inplace= True)

        self.clusters[cluster_id] = cluster_df

        # Publishing for every hour
        if(datetime.timestamp(timestamps[-1]) - datetime.timestamp(self.timestamp)) > 3600:
            # self.print_values(self.clusters, timestamp[-1])
            self.timestamp = timestamps[-1]
            # self.publish(self.clusters)
            for clust_id in self.clusters.keys():
                count_frame = self.count_alert_per_cluster(self.clusters[clust_id])
                #self.print_corr(count_frame, clust_id)
                # self.publish(count_frame)
                corr_frame = self.corr_over_time(count_frame)
                # self.print_corr(corr_frame, clust_id, ops='Correlation')

                # 1-D vector generation
                L = list(corr_frame.columns.values)
                mask = np.zeros_like(corr_frame, dtype=np.bool)
                mask[np.triu_indices_from(mask)] = True
                corr_frame = corr_frame.mask(mask)

                alert_combination_list = []
                alert_combination_value_list = []
                for elm in list(combinations(L, 2)):
                    try:
                        val = corr_frame.get_value(index=elm[1], col=elm[0])

                    except KeyError:
                        val = math.nan
                    alert_combination_list.append('_'.join(elm))
                    alert_combination_value_list.append(val)

                tuple_timestamp = time.mktime(self.timestamp.timetuple())
                self.clusters_correlation[clust_id] = {'dataframe': pd.DataFrame(data = [alert_combination_value_list],
                                                                    columns = alert_combination_list),
                                                       'version': version_id,
                                                       'timestamp': tuple_timestamp}

            self.publish(self.clusters_correlation)
            #self.publish(cluster_id)

    @staticmethod
    def print_values(dataframe_dict, timestamp):
        print("Printing for :", timestamp)
        for key in dataframe_dict.keys():
            print("Cluster_id:", key, " in timestamp:", timestamp)
            print(dataframe_dict[key])
        return None

    def alert_name(self, x):
        """
        Returns alert name of current stream
        :param x:
        :return:
        """
        return self.metric_label(x, 'alertname')

    def count_alert_per_cluster(self, cluster_frame):
        """
        This method counts the number of alert happening, given a time interval, on evry delta of it
        :param cluster_frame:
        :return:
        """

        df_filtered = cluster_frame
        df_filtered['value'] = 1
        df_count_half_hour = pd.DataFrame()
        for alert_name in list(df_filtered['alertname'].unique()):
            grouped_frame = ((df_filtered[df_filtered['alertname'] == alert_name]).groupby(
                pd.Grouper(key='timestamp', freq='30min')).count())
            df_count_half_hour[alert_name] = grouped_frame['value']
        df_count_half_hour['timestamp'] = (df_filtered.groupby(
                pd.Grouper(key='timestamp', freq='30min')).count()).index.values
        df_count_half_hour.reset_index(drop=True, inplace=True)
        return df_count_half_hour

    def corr_over_time(self, cluster_frame):
        """
        Calculate correlation between alerts
        :param cluster_frame:
        :return: correlation frame
        """
        return cluster_frame[cluster_frame.columns.difference(['timestamp'])].corr()

    def print_corr(self, cluster_frame, cluster_id, ops = 'Value'):
        """
        Print correlation or count matrix/frame depending on ops
        :param cluster_frame:
        :param cluster_id:
        :param ops:
        :return:
        """
        print("Printing" + ops + " for :", cluster_id)
        print(cluster_frame.head())