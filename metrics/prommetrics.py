import json
import os
import sys
import dateparser

from rx import Observable

#Prometheus connection stuff
from prometheus import Prometheus


# Scheduling stuff
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

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
        
    def _get_metrics_from_prometheus(self, observer=None):
        # Collect credentials to connect to a prometheus instance
        prom_token = os.getenv("PROM_ACCESS_TOKEN")
        prom_url = os.getenv("PROM_URL")
        if not (prom_token or prom_url):
            sys.exit("Error: Prometheus credentials not found")


        prom = Prometheus(url=prom_url, token=prom_token, data_chunk='5m',stored_data='5m')

        metrics_list = prom.all_metrics() # Get a list of all the metrics available from Prometheus

        print("Polling Prometheus for new metric data")

        metric_data = dict()
        if observer:
            for metric in metrics_list:
                pkt = (json.loads(prom.get_metric(name=metric))[0])
                metric_data[metric] = pkt
                observer.on_next(pkt) # push metric data to the Observer
            pass
        else:
            for metric in metrics_list:
                metric_data[metric] = (json.loads(prom.get_metric(name=metric))[0])

        return(metric_data)

    def observe_prom_metrics_range(self, observer, metrics_list, start_time, end_time='now', chunk_size='1h'):

        # Collect credentials to connect to a prometheus instance
        prom_token = os.getenv("PROM_ACCESS_TOKEN")
        prom_url = os.getenv("PROM_URL")
        if not (prom_token or prom_url):
            sys.exit("Error: Prometheus credentials not found")


        prom = Prometheus(url=prom_url, token=prom_token)

        chunk_seconds = int(round((dateparser.parse('now') - dateparser.parse(chunk_size)).total_seconds()))


        start = dateparser.parse(start_time).timestamp()
        end = dateparser.parse(end_time).timestamp()

        while start <= end:

            for metric_name in metrics_list:

                pkt_list = json.loads(prom.get_metric_range_data(metric_name=metric_name, start_time=start, end_time=end))
                for pkt in pkt_list:
                    try:
                        observer.on_next(pkt)
                    except Exception as e:
                        print(pkt)
                        raise(e)

            start += chunk_seconds

        pass
