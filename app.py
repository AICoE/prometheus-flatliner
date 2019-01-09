import flatliners
import metrics
import os
from time import sleep

def main():
    metrics_list = os.getenv("FLT_METRICS_LIST")
    if metrics_list:    # If the env variable for FLT_METRICS_LIST is set, pull data from Prometheus
        metrics_list = str(metrics_list).split(",")
        print("The metrics initialized were: ",metrics_list)
        metric_start_datetime = os.getenv("FLT_METRIC_START_DATETIME","16 Oct 2018")
        metric_end_datetime = os.getenv("FLT_METRIC_END_DATETIME","17 Oct 2018")
        metric_chunk_size = os.getenv("FLT_METRIC_CHUNK_SIZE","15m")

        if os.getenv("FLT_LIVE_METRIC_COLLECT","False") == "True":
            print("Live Metrics Collection Mode")
            # metrics_observable is an observable that streams in all the data alerts->etcd->build
            metrics_observable = metrics.PromMetricsLive(metrics_list=metrics_list,
                                                        metric_chunk_size=metric_chunk_size)
        else:
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

    std_dev_cluster = flatliners.StdDevCluster()  # this is an observer that operates on some cluster data
    std_dev_version = flatliners.StdDevVersion()  # this is an observer that operates on some version data
    comparison_score = flatliners.ComparisonScore()

    single_value_metric = flatliners.SingleValueMetric()
    versioned_metrics.subscribe(single_value_metric)

    # take etcd data and perform std_dev_cluster operation
    single_value_metric.subscribe(std_dev_cluster)
    std_dev_cluster.subscribe(std_dev_version)

    # std_dev_cluster emits the std_dev for a cluster
    # this is something std_dev_version is interested in
    std_dev_cluster.subscribe(comparison_score)
    std_dev_version.subscribe(comparison_score)

    weirdness_score = flatliners.WeirdnessScore()
    comparison_score.subscribe(weirdness_score)
    # corr_comparison_score.subscribe(weirdness_score)

    # weirdness_score.subscribe(print)

    score_sum = 0
    def add_scores(value):
        nonlocal score_sum
        score_sum = score_sum + value.std_dev

    weirdness_score.subscribe(add_scores)

    if os.getenv("FTL_INFLUX_DB_DSN"):
        influxdb_storage = flatliners.InfluxdbStorage(os.environ.get("FTL_INFLUX_DB_DSN"))
        weirdness_score.subscribe(influxdb_storage)

    # connect the metrics stream to publish data
    metrics_observable.connect()

    if os.getenv("FLT_LIVE_METRIC_COLLECT","False") == "True":
        while True:
            sleep(60) # This should be replaced by a flask app that serves weirdness_score as a metric

    return score_sum # This score sum is different for different chunk sizes, we might wanna look into different metrics for this


if __name__ == '__main__':
    print(main())
