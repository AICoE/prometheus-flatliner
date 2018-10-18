import bz2
import json
import os

from rx import Observable


class FileMetrics:
    def __init__(self):
        self.observable = Observable.create(self.push_metrics).publish()

    def subscribe(self, observer):
        self.observable.subscribe(observer)

    def connect(self):
        self.observable.connect()

    def push_metrics(self, observer):
        self.load_files(observer)
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
