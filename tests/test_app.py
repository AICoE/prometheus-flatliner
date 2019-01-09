import app


class TestApp():

    def test_metric_label(self):
        score_sum = app.main()
        assert score_sum == 50381.69746040763
