from flatliners import StdDevVersion


class TestStdDevVersion():

    def test_initilize_calculate_version_std(self):

        sdv = StdDevVersion()

        value = 5
        resource = 'resource1'
        version = ' 1.0'

        version_info =  sdv.calculate_version_std(value, resource, version)

        assert version_info.avg_std_dev == 5
        assert version_info.count == 1
        assert version_info.total == 5

    def test_continue_calculate_version_std(self):

        sdv = StdDevVersion()

        value = 5
        resource = 'resource1'
        version = ' 1.0'
        previous = sdv.State()
        previous.version = '1.0'
        previous.resource = 'resource1'
        previous.avg_std_dev = 5
        previous.count = 1
        previous.total = 5

        version_info = sdv.calculate_version_std(value, resource, version, previous)

        assert version_info.avg_std_dev == 5
        assert version_info.count == 2
        assert version_info.total == 10




