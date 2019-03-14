import flatliners
import metrics
import os
import dateparser
from time import sleep
import logging

# Set up logging
_LOGGER = logging.getLogger(__name__)

if os.getenv("FLT_DEBUG_MODE","False") == "True":
    logging_level = logging.DEBUG # Enable Debug mode
else:
    logging_level = logging.INFO

# Log record format
logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s', level=logging_level)

def main():
    metrics_list = os.getenv("FLT_METRICS_LIST")
    if metrics_list:    # If the env variable for FLT_METRICS_LIST is set, pull data from Prometheus
        metrics_list = str(metrics_list).split(",")
        _LOGGER.info("The metrics initialized were: {0}".format(metrics_list))
        metric_start_datetime = os.getenv("FLT_METRIC_START_DATETIME","16 Oct 2018")
        metric_end_datetime = os.getenv("FLT_METRIC_END_DATETIME","17 Oct 2018")
        metric_chunk_size = os.getenv("FLT_METRIC_CHUNK_SIZE","15m")

        if os.getenv("FLT_LIVE_METRIC_COLLECT","False") == "True":
            _LOGGER.info("Starting Live Metrics Collection Mode")
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
    comparison_score = flatliners.ResourceComparisonScore()

    alert_freq_cluster = flatliners.AlertFrequencyCluster()
    alert_freq_version = flatliners.AlertFrequencyVersion()
    alert_comparison = flatliners.AlertComparisonScore()

    single_value_metric = flatliners.SingleValueMetric()
    versioned_metrics.subscribe(single_value_metric)

    single_value_metric.subscribe(alert_freq_cluster)
    alert_freq_cluster.subscribe(alert_freq_version)

    alert_freq_version.subscribe(alert_comparison)
    alert_freq_cluster.subscribe(alert_comparison)

    # take etcd data and perform std_dev_cluster operation
    single_value_metric.subscribe(std_dev_cluster)
    std_dev_cluster.subscribe(std_dev_version)

    # std_dev_cluster emits the std_dev for a cluster
    # this is something std_dev_version is interested in
    std_dev_cluster.subscribe(comparison_score)
    std_dev_version.subscribe(comparison_score)

    weirdness_score = flatliners.WeirdnessScore()
    comparison_score.subscribe(weirdness_score)
    alert_comparison.subscribe(weirdness_score)

    # weirdness_score.subscribe(print)

    score_sum = 0

    def add_scores(value):
        nonlocal score_sum
        if isinstance(value, flatliners.weirdnessscore.WeirdnessScore.Resource_State):
            score_sum = score_sum + value.std_dev

    weirdness_score.subscribe(add_scores)

    if os.getenv("FLT_INFLUX_DB_DSN"):
        influxdb_storage = flatliners.InfluxdbStorage(os.environ.get("FLT_INFLUX_DB_DSN"))
        weirdness_score.subscribe(influxdb_storage)

    if os.getenv("FLT_LIVE_METRIC_COLLECT","False") == "True":
        # Published Stale metrics are removed once every three times metric data is collected from prometheus
        metric_pruning_interval = 3 * round((dateparser.parse('now')-dateparser.parse(os.getenv("FLT_METRIC_CHUNK_SIZE","5m"))).total_seconds())

        prom_endpoint = flatliners.PrometheusEndpoint(pruning_interval=metric_pruning_interval)
        weirdness_score.subscribe(prom_endpoint)

        # connect the metrics stream to publish data
        metrics_observable.connect()

        prom_endpoint.start_server() # this method never returns, starts a web server
    else:
        # connect the metrics stream to publish data
        metrics_observable.connect()

        return score_sum


if __name__ == '__main__':
    print(main())
