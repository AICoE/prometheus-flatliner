import os
import sys
import dateparser

from rx import Observable

#Prometheus connection stuff
from prometheus import Prometheus

from metrics import PromMetrics

# Scheduling stuff
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

class PromMetricsLive:
    def __init__(self, metrics_list, metric_chunk_size='1h'):
        self.observable = Observable.create(self.push_metrics).publish()
        self.metrics_list = metrics_list
        self.metric_end_datetime = 'now'
        self.metric_chunk_size = metric_chunk_size

    def subscribe(self, observer):
        self.observable.subscribe(observer)

    def connect(self):
        self.observable.connect()

    def push_metrics(self, observer):
        self._get_metrics_from_prometheus(observer) # Initial run for metric collection

        # Scheduler schedules a background job that needs to be run regularly
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(
            func=lambda: self._get_metrics_from_prometheus(observer), # Run this function every 5 minutes to poll for new metric data
            trigger=IntervalTrigger(seconds=int(round((dateparser.parse('now') - dateparser.parse(self.metric_chunk_size)).total_seconds()))),
            id='update_metric_data',
            name='Ticker to collect new data from prometheus',
            replace_existing=True)

        atexit.register(lambda: scheduler.shutdown()) # Shut down the scheduler when exiting the app

    def _get_metrics_from_prometheus(self, observer):
        # Use the existing PromMetrics Class to push metrics to the observer
        PromMetrics(metrics_list=self.metrics_list,
                    metric_start_datetime=self.metric_chunk_size,
                    metric_end_datetime=self.metric_end_datetime,
                    metric_chunk_size=self.metric_chunk_size).push_metrics(observer=observer)
