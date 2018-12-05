from flatliners import StdDevCluster
import numpy as np
from statistics import stdev

class TestStdDevCluster():


    def test_single_entry_initilize_calculation(self):

        sdc = StdDevCluster()
        x = [[0,'5']]

        count, mean, total, std_dev, m2 = sdc.initilize_calculation(x)

        assert count == 1
        assert mean == 5
        assert total == 5
        assert std_dev == 0
        assert m2 == 0

    def test_multiple_entry_initilize_calculation(self):

        sdc = StdDevCluster()
        x = [[0, '5'], [0, '10'], [0, '25']]

        count, mean, total, std_dev, m2 = sdc.initilize_calculation(x)

        assert count == 3
        assert mean == np.mean([5, 10, 25])
        assert total == sum([5, 10, 25])
        assert std_dev == stdev([5, 10, 25])
        assert m2 == sum((np.array([5, 10, 25]) - mean)**2)


    def test_continue_calculation(self):

        sdc = StdDevCluster()

        previous = {'count': 2, 'total': 10, 'mean': 5,
                    'm2': 0, 'std_dev': 0}

        x = [[0, '0']]

        count, mean, total, std_dev, m2 = sdc.continue_calculation(x, previous)

        assert count == 3
        assert mean == np.mean([5, 5, 0])
        assert total == 10
        assert std_dev == stdev([0, 5, 5])
        assert m2 == sum((np.array([0,5, 5]) - mean)**2)







