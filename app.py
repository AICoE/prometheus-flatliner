import flatliners
import metrics

if __name__ == '__main__':
    metrics = metrics.FileMetrics()
    # subscribe versioned metrics, which adds the version to the metrics stream
    # to metrics. Every metric emitted by metrics is sent to versioned_metrics
    versioned_metrics = flatliners.VersionedMetrics()
    metrics.subscribe(versioned_metrics)

    # # just 2 flatliners
    # std_dev_cluster = flatliners.StdDevCluster()
    # std_dev_version = flatliners.StdDevVersion()
    #
    # # one will get versioned metrics
    # versioned_metrics.subscribe(std_dev_cluster)
    #
    # # std_dev_cluster emits the std_dev for a cluster
    # # this is something std_dev_version is interested in
    # std_dev_cluster.subscribe(std_dev_version)
    # std_dev_version.subscribe(print)
    df_gen = flatliners.DfGenerator()
    versioned_metrics.subscribe(df_gen)
    df_gen.subscribe(print)
    # df_gen.on_completed()
    # print(df)
    metrics.connect()
