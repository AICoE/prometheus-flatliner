from flatliners import BaseFlatliner


class TestBaseflatliner():

    def test_metric_label(self):
        bf = BaseFlatliner()
        metric = {'metric': {'label': 'label_value'}}

        assert bf.metric_label(metric, 'label') == 'label_value'
