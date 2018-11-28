import bz2
import json
import os

from rx import Observable

# Scheduling stuff
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

class FileMetrics:
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
            func=lambda: self.load_files(observer), # Run this function every 10 seconds to poll for new metric data
            trigger=IntervalTrigger(seconds=10),
            id='update_metric_data',
            name='Ticker to get new data from prometheus',
            replace_existing=True)

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())
        # self.load_files(observer)
        # observer.on_next(randint(1, 10000000))

    def load_files(self, observer):
        print("loading files")
        files = []
        folder = 'data'
        for root, d_names, f_names in os.walk(folder):
            for f in f_names:
                if f.endswith('bz2') or f.endswith('json'):
                    files.append(os.path.join(root, f))
        files.sort()
        print("Processing %s files" % len(files))

        for file in files:
            # check file format and read appropriately
            if file.endswith('json'):
                f = open(file, 'rb')
            else:
                f = bz2.BZ2File(file, 'rb')

            jsons = json.load(f)
            for pkt in jsons:
                observer.on_next(pkt)

            f.close()
