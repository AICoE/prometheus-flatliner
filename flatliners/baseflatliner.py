from rx import Observer
from rx.subjects import Subject

from cachetools import TTLCache

class BaseFlatliner(Observer):
    subject = None

    def __init__(self):
        self.subject = Subject()

    def on_next(self, x):
        print("Got: %s" % x)

    def on_error(self, e):
        print("Got error: %s" % e)

    def on_completed(self):
        print("Sequence completed")

    def publish(self, value):
        self.subject.on_next(value)

    def subscribe(self, observer):
        print(f"Subscribing {observer} to {self}")
        self.subject.subscribe(observer)

    @staticmethod
    def metric_label(metric, name):
        return metric['metric'].get(name, None)

    @staticmethod
    def metric_values(x):
        return x['values']

    def metric_name(self, x):
        return self.metric_label(x, '__name__')

    def cluster_id(self, x):
        return self.metric_label(x, '_id')

    def cluster_version(self, x):
        return self.metric_label(x, 'version')

    @staticmethod
    def create_cache_dict(maxsize=2000, ttl=900):
        # maxsize determines the maximum number of elements inside the dictionary
        # if new elements are added when its full, it will act as a LRUCache.

        # ttl determines the time to live for each element in the dictionary, so
        # $(ttl) seconds after the element is added, it will be marked for deletion
        # if the element is updated, the timer resets.
        return TTLCache(maxsize=maxsize, ttl=ttl)
