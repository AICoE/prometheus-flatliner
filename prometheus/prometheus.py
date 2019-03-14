from urllib.parse import urlparse
import requests
import datetime
import dateparser
import sys
from retrying import retry

# Disable SSL warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Prometheus:
    """docstring for Prometheus."""
    def __init__(self, url='', token=None):
        self.headers = { 'Authorization': "bearer {}".format(token) }
        self.url = url
        self.prometheus_host = urlparse(self.url).netloc

    @retry(stop_max_attempt_number=3)
    def get_metric_range_data(self, metric_name, start_time, end_time='now', chunk_size=None,label_config=None):
        data = []

        start = int(dateparser.parse(str(start_time)).timestamp())
        end = int(dateparser.parse(str(end_time)).timestamp())

        if not chunk_size:
            chunk_seconds = int(end - start)
            chunk_size = str(int(chunk_seconds)) + "s"
        else:
            chunk_seconds = int(round((dateparser.parse('now') - dateparser.parse(chunk_size)).total_seconds()))

        if int(end-start) < chunk_seconds:
            sys.exit("specified chunk_size is too big")

        if label_config:
            label_list = [str(key+"="+ "'" + label_config[key]+ "'") for key in label_config]
            # print(label_list)
            query = metric_name + "{" + ",".join(label_list) + "}"
        else:
            query = metric_name

        while start < end:
            # print(chunk_size)
            response = requests.get('{0}/api/v1/query'.format(self.url),    # using the query API to get raw data
                                params={'query': query + '[' + chunk_size + ']',
                                        'time': start + chunk_seconds
                                        },
                                verify=False, # Disable ssl certificate verification temporarily
                                headers=self.headers)
            if response.status_code == 200:
                data += response.json()['data']['result']
            else:
                raise Exception("HTTP Status Code {} {} ({})".format(
                    response.status_code,
                    requests.status_codes._codes[response.status_code][0],
                    response.content
                ))
            start += chunk_seconds
        return (data)
