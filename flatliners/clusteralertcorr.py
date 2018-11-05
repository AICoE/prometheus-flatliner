import math
import pandas as pd
from datetime import datetime
from .baseflatliner import BaseFlatliner

class ClusterAlertCorrelation(BaseFlatliner):

    '''
    This class contains the code for correlation of alerts for every cluster

    '''

    def __init__(self):
        print(" Inside alert corr")
        super().__init__()
        ## Hold the values for different clusters
        self.clusters = dict()
        #TODO : save correlation over time
        self.clusters_correlation = dict()
        ### To keep track of previous publish
        self.timestamp = datetime.fromtimestamp(0)

    def on_next(self, x):
        """ On each data loading it will create dataframe and then pivot frame
        """
        # print(f"got {x}")

        if not self.metric_name(x) == 'alerts':
            return

        alert_name = self.metric_label(x, 'alertname')
        cluster_id = self.cluster_id(x)

        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = pd.DataFrame(columns=['_id', 'timestamp', 'alertname'])
            self.clusters_correlation[cluster_id] = pd.DataFrame()

        previous_df = self.clusters[cluster_id]

        ### Dataframe creation
        timestamp = []
        cluster = []
        alert_name_list = []

        for elem in self.metric_values(x):
            timestamp.append(datetime.fromtimestamp(elem[0]))
            cluster.append(cluster_id)
            alert_name_list.append(alert_name)
        df = previous_df.append\
            (pd.DataFrame({'_id': cluster, 'timestamp': timestamp, 'alertname': alert_name_list}))
        df.reset_index(drop= True, inplace= True)

        self.clusters[cluster_id] = df


        ### Publishing for every hour
        if(datetime.timestamp(timestamp[-1]) - datetime.timestamp(self.timestamp)) > 3600:
            self.print_values(self.clusters, timestamp[-1])
            self.timestamp = timestamp[-1]
            self.publish(self.clusters)
            for clust_id in self.clusters.keys():
                count_frame = self.count_alert_per_cluster(self.clusters[clust_id])
                self.print_corr(count_frame, clust_id)
                self.publish(count_frame)
                corr_frame = self.corr_over_time(count_frame)
                print("Alert correlation of cluster:", clust_id, " in timestamp:", timestamp[-1],\
                      corr_frame)
                self.print_corr(corr_frame, clust_id, ops='Correlation')
                self.publish(corr_frame)



    def on_completed(self):
        #print(self.clusters)
        print("Done!")


    @staticmethod
    def print_values(dataframe_dict, timestamp):
        print("Printing for :", timestamp)
        for key in dataframe_dict.keys():
            print("Cluster_id:", key, " in timestamp:", timestamp)
            print(dataframe_dict[key])
        return None

    def alert_name(self, x):
        '''
        Returns alert name of current stream
        :param x:
        :return:
        '''
        return self.metric_label(x, 'alertname')

    def count_alert_per_cluster(self, cluster_frame):
        '''
        This method counts the number of alert happening, given a time interval, on evry delta of it
        :param cluster_frame:
        :return:
        '''

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
        '''
        Calculate correlation between alerts
        :param cluster_frame:
        :return: correlation frame
        '''
        return cluster_frame[cluster_frame.columns.difference(['timestamp'])].corr()

    def print_corr(self, cluster_frame, cluster_id, ops = 'Value'):
        '''
        Print correlation or count matrix/frame depending on ops
        :param cluster_frame:
        :param cluster_id:
        :param ops:
        :return:
        '''
        print("Printing" + ops + " for :", cluster_id)
        print(cluster_frame.head())


