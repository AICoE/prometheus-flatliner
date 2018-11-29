import json
import os

from rx import Observable

#Prometheus connection stuff
from prometheus import Prometheus

# Scheduling stuff
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

class PromMetrics:
    def __init__(self):
        self.observable = Observable.create(self.push_metrics).publish()

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
            trigger=IntervalTrigger(minutes=5),
            id='update_metric_data',
            name='Ticker to get new data from prometheus',
            replace_existing=True)

        atexit.register(lambda: scheduler.shutdown()) # Shut down the scheduler when exiting the app

    def _get_metrics_from_prometheus(self, observer):
        # Collect credentials to connect to a prometheus instance
        prom_token = os.getenv("PROM_ACCESS_TOKEN",None)
        prom_url = os.getenv("PROM_URL",None)
        if not (prom_token or prom_url):
            print("Prometheus credentials not found")
            exit(0)


        prom = Prometheus(url=prom_url, token=prom_token, data_chunk='5m',stored_data='5m')

        metrics_list = prom.all_metrics() # Get a list of all the metrics available from Prometheus

        print("Polling Prometheus for new metric data")

        for metric in metrics_list:
            pkt = (json.loads(prom.get_metric(name=metric))[0])
            observer.on_next(pkt) # push metric data to the Observer
        pass
