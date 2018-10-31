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

    def alert_name(self, x):
        return self.metric_label(x, 'alertname')

    ## Correlation change calculation for every Git version

    ## TODO: The caller part and pivot frame
    def corr_change_over_build_and_time(git_version):
        low = 0
        timestamp_l = []
        pivot_group = pivot_frame_dict[git_version]
        if pivot_group is None:
            return None, None

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

        # corr_change_frame = pd.DataFrame({'timestamp':timestamp_l, 'corr_change': corr_change_l})
        git_version_corr_shift = pd.DataFrame(element_dict)

        return git_version_corr_shift