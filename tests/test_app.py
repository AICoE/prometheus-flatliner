import app


class TestApp():

    def test_metric_label(self):
        score_sum = app.main()
        assert score_sum == 104258.41245185716
