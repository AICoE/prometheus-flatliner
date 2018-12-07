import json
import os
import sys
import dateparser

from rx import Observable

#Prometheus connection stuff
from prometheus import Prometheus

<<<<<<< HEAD
=======

# Scheduling stuff
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

>>>>>>> fdffd6e28266f2c36743fe0495315ca62055e1e8
class PromMetrics:
    def __init__(self, metrics_list, metric_start_datetime='1h', metric_end_datetime='now', metric_chunk_size='1h'):
        self.observable = Observable.create(self.push_metrics).publish()
        self.metrics_list = metrics_list
        self.metric_start_datetime = metric_start_datetime
        self.metric_end_datetime = metric_end_datetime
        self.metric_chunk_size = metric_chunk_size

    def subscribe(self, observer):
        self.observable.subscribe(observer)

    def connect(self):
        self.observable.connect()

    def push_metrics(self, observer):
        self.observe_prom_metrics_range(observer=observer,
                                        metrics_list=self.metrics_list,
                                        start_time=self.metric_start_datetime,
                                        end_time=self.metric_end_datetime,
                                        chunk_size=self.metric_chunk_size)

    def observe_prom_metrics_range(self, observer, metrics_list, start_time, end_time='now', chunk_size='1h'):
        # Collect credentials to connect to a prometheus instance
        prom_token = os.getenv("FLT_PROM_ACCESS_TOKEN")
        prom_url = os.getenv("FLT_PROM_URL")
        if not (prom_token or prom_url):
            sys.exit("Error: Prometheus credentials not found")
        prom = Prometheus(url=prom_url, token=prom_token)

        # Calculate chunk size to download and push to the observer at each instance
        chunk_seconds = int(round((dateparser.parse('now') - dateparser.parse(chunk_size)).total_seconds()))
        print("Collecting metric data within datetime range:{0} - {1}".format(dateparser.parse(start_time),dateparser.parse(end_time)))
        start = dateparser.parse(start_time).timestamp()
        end = dateparser.parse(end_time).timestamp()

        while start <= end:     # Main loop which iterates through time-ranges to collect a chunk of data at every iteration
            for metric_name in metrics_list:    # Loop to get a chunk of data for every metric in the list
                pkt_list = (prom.get_metric_range_data(metric_name=metric_name, start_time=start, end_time=end))

                for pkt in pkt_list:        # pkt_list contains a list of data for multiple metrics, each of which is pushed to the observer.
                    try:
                        observer.on_next(pkt)
                    except Exception as e:
                        print(pkt) # Check which pkt caused the exception
                        raise(e)
            start += chunk_seconds
        pass
