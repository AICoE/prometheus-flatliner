import flatliners
import metrics

if __name__ == '__main__':
    metrics = metrics.FileMetrics() # this is an observable that streams in all the data alerts->etcd->build

    # subscribe versioned metrics, which adds the version to the metrics stream
    # to metrics. Every metric emitted by metrics is sent to versioned_metrics
    versioned_metrics = flatliners.VersionedMetrics() # initilizes an observer that operates on our data
    metrics.subscribe(versioned_metrics) # creates versioned_metrics that adds version to etcd data


    # just 2 flatliners
    std_dev_cluster = flatliners.StdDevCluster() # this is an observer that operates on some cluster data
    std_dev_version = flatliners.StdDevVersion() # this is an observer that operates on some version data
    comparison_score = flatliners.ComparisonScore()

    # one will get versioned metrics
    versioned_metrics.subscribe(std_dev_cluster) # take etcd data and perform std_dev_cluster operation
    std_dev_cluster.subscribe(std_dev_version)

    # std_dev_cluster emits the std_dev for a cluster
    # this is something std_dev_version is interested in

    std_dev_cluster.subscribe(comparison_score)
    std_dev_version.subscribe(comparison_score)
    comparison_score.subscribe(print)

    # Alert correlation
    alert_cor = flatliners.ClusterAlertCorrelation()
    versioned_metrics.subscribe(alert_cor)
    alert_cor.subscribe(print)

    # connect the metrics stream to publish data
    metrics.connect()
    