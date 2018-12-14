from .baseflatliner import BaseFlatliner

class SingleValueMetric(BaseFlatliner):

    def __init__(self):
        super().__init__()

    def on_next(self, x):

        for value in x['values']:
            single_value_metric = x
            single_value_metric['values'] = [value]
            self.publish(single_value_metric)