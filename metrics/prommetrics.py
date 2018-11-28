import bz2
import json
import os

from rx import Observable

from prometheus import Prometheus

import time # remove later

# Scheduling stuff
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

class PromMetrics:
    """docstring for PromMetrics."""
    def __init__(self):
        self.observable = Observable.create(self.push_metrics).publish()

    def subscribe(self, observer):
        self.observable.subscribe(observer)

    def connect(self):
        self.observable.connect()

    def push_metrics(self, observer):
        # Scheduler schedules a background job that needs to be run regularly
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(
            func=lambda: self.get_metric_from_prometheus(observer), # Run this function every 10 seconds to poll for new metric data
            trigger=IntervalTrigger(seconds=100),
            id='update_metric_data',
            name='Ticker to get new data from prometheus',
            replace_existing=True)

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
        # self.get_metric_from_prometheus(observer)


    def get_metric_from_prometheus(self, observer):
        print("Polling Prometheus for new metric data")
        prom_token = os.getenv("PROM_ACCESS_TOKEN")
        prom_url = os.getenv("PROM_URL")
        prom = Prometheus(url=prom_url, token=prom_token, data_chunk='5m',stored_data='5m')

        # while True:
        metrics_list = prom.all_metrics()
        # time.sleep(60)
        # metrics_list = ["up"]
        for metric in metrics_list:
            pkt = (json.loads(prom.get_metric(name=metric))[0])
            pkt['metric']['_id'] = "dummy_id"
            pkt['metric']['cluster'] = "dummy_cluster"
            pkt['metric']['gitVersion'] = "dummy_git_version"
            print(pkt)
            observer.on_next(pkt)

            # pass
        pass
