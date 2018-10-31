from rx import Observer
from rx.subjects import Subject


class BaseFlatliner(Observer):
    subject = None

    def __init__(self):
        print("base init")
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
        return metric['metric'][name]

    @staticmethod
    def metric_values(x):
        return x['values']

    def metric_name(self, x):
        return self.metric_label(x, '__name__')

    def cluster_id(self, x):
        return self.metric_label(x, '_id')

    def get_version(self, x):
        return self.metric_label(x, 'gitVersion')

