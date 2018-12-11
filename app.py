import flatliners
import metrics
import os


def main():
    metrics_list = os.getenv("FLT_METRICS_LIST")
    if metrics_list:    # If the env variable for FLT_METRICS_LIST is set, pull data from Prometheus
        metrics_list = str(metrics_list).split(",")
        print("The metrics initialized were: ",metrics_list)
        metric_start_datetime = os.getenv("FLT_METRIC_START_DATETIME","16 Oct 2018")
        metric_end_datetime = os.getenv("FLT_METRIC_END_DATETIME","17 Oct 2018")
        metric_chunk_size = os.getenv("FLT_METRIC_CHUNK_SIZE","6h")

        metrics_observable = metrics.PromMetrics(metrics_list=metrics_list,
                                    metric_start_datetime=metric_start_datetime,
                                    metric_end_datetime=metric_end_datetime,
                                    metric_chunk_size=metric_chunk_size) # this is an observable that streams in all the data alerts->etcd->build

    else:                       # If FLT_METRICS_LIST is not set, use data from '/data/*'
        metrics_observable = metrics.FileMetrics()  # this is an observable that streams in all the data alerts->etcd->build

    # subscribe versioned metrics, which adds the version to the metrics stream
    # to metrics. Every metric emitted by metrics is sent to versioned_metrics
    versioned_metrics = flatliners.VersionedMetrics()  # initilizes an observer that operates on our data
    metrics_observable.subscribe(versioned_metrics)  # creates versioned_metrics that adds version to etcd data

    # just 2 flatliners
    std_dev_cluster = flatliners.StdDevCluster()  # this is an observer that operates on some cluster data
    std_dev_version = flatliners.StdDevVersion()  # this is an observer that operates on some version data
    comparison_score = flatliners.ComparisonScore()
    corr_comparison_score = flatliners.CorrComparisonScore()

    # one will get versioned metrics
    versioned_metrics.subscribe(std_dev_cluster)  # take etcd data and perform std_dev_cluster operation
    std_dev_cluster.subscribe(std_dev_version)

    # std_dev_cluster emits the std_dev for a cluster
    # this is something std_dev_version is interested in

    std_dev_cluster.subscribe(comparison_score)
    std_dev_version.subscribe(comparison_score)
    # comparison_score.subscribe(print)

    # Alert correlation
    alert_cor = flatliners.ClusterAlertCorrelation()
    versioned_metrics.subscribe(alert_cor)
    # alert_cor.subscribe(print) # this emits a df with the correlation values for a single cluster

    # Git version alert correlation
    version_alert_corr = flatliners.GitVersionAlertCorrelation()

    versioned_metrics.subscribe(version_alert_corr)
    # version_alert_corr.subscribe(print) # this emits a df with correlation values for a gitVersion

    alert_cor.subscribe(corr_comparison_score)

    version_alert_corr.subscribe(corr_comparison_score)

    # corr_comparison_score.subscribe(print)

    weirdness_score = flatliners.WeirdnessScore()
    comparison_score.subscribe(weirdness_score)
    corr_comparison_score.subscribe(weirdness_score)

    # weirdness_score.subscribe(print)

    score_sum = 0
    def add_scores(value):
        nonlocal score_sum
        score_sum = score_sum + value['corr']

    # weirdness_score.subscribe(lambda value: count = count + 1)
    weirdness_score.subscribe(add_scores)

    if "FLT_INFLUX_HOST" in os.environ:
        influxdb_storage = flatliners.InfluxdbStorage()
        weirdness_score.subscribe(influxdb_storage)

    # connect the metrics stream to publish data
    metrics_observable.connect()

    return score_sum # This score sum is different for different chunk sizes, we might wanna look into different metrics for this


if __name__ == '__main__':
    print(main())
