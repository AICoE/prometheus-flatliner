from .baseflatliner import BaseFlatliner
import pandas as pd
from datetime import datetime


class AlertCorrelation(BaseFlatliner):
    '''
    This class contains the code for correlation of alerts

    '''

    def __init__(self):
        print(" Inside alert corr")
        super().__init__()
        ## Hold the values for different clusters
        self.clusters = dict()
        ### Empty dataframe placeholder
        self.df = pd.DataFrame(columns=['_id', 'timestamp', 'alertname', 'gitversion'])
        ### To keep track of previous publish
        self.timestamp = 0

    def on_next(self, x):
        """ On each data loading it will create dataframe and then pivot frame
        """
        # print(f"got {x}")

        if not self.metric_name(x) == 'alerts':
            return

        alert_name = self.metric_label(x, 'alertname')
        cluster_id = self.cluster_id(x)
        git_version = self.get_version(x)

        if cluster_id not in self.clusters:
            self.clusters[cluster_id] = dict()

        if alert_name not in self.clusters[cluster_id]:
            self.clusters[cluster_id][alert_name] = self.metric_values(x)

        else:
            previous = self.clusters[cluster_id][alert_name]
            previous.extend(self.metric_values(x))
            self.clusters[cluster_id][alert_name] = previous
        previous_df = self.df

        ### Dataframe creation
        timestamp = []
        cluster = []
        alert_name_list = []
        git_version_list = []

        for elem in self.metric_values(x):
            timestamp.append(elem[0])
            cluster.append(cluster_id)
            alert_name_list.append(alert_name)
            git_version_list.append(git_version)
        self.df = previous_df.append\
            (pd.DataFrame({'_id': cluster, 'timestamp': timestamp, 'alertname': alert_name_list, 'gitversion': git_version_list}))
        self.df.reset_index(drop= True, inplace= True)


        ### Publishing for every hour
        if(timestamp[-1] - self.timestamp) > 3600:
            self.print_values(self.df, timestamp[-1])
            self.timestamp = timestamp[-1]
            self.publish(self.df)


    def on_completed(self):
        #print(self.clusters)
        print("Done!")


    @staticmethod
    def print_values(dataframe, timestamp):
        print("Printing for :", datetime.fromtimestamp(timestamp))
        print(dataframe.tail(6))
        return None