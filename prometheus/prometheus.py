from urllib.parse import urlparse
import requests
import datetime
import json
import time
import dateparser
import sys
from retrying import retry

# Disable SSL warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DEBUG = False
MAX_REQUEST_RETRIES = 5
CONNECTION_RETRY_WAIT_TIME = 5

class Prometheus:
    """docstring for Prometheus."""
    def __init__(self, url='', end_time=None, token=None, data_chunk='1h',stored_data='1h'):
        self.headers = { 'Authorization': "bearer {}".format(token) }
        self.url = url
        self.prometheus_host = urlparse(self.url).netloc
        self._all_metrics = None
        self.data_chunk_size = data_chunk
        self.end_time = datetime.datetime.now()
        self.stored_data_range = stored_data
        self.DATA_CHUNK_SIZE_LIST = {
            '1m' : 60,
            '3m' : 180,
            '5m' : 300,
            '30m': 1800,
            '1h' : 3600,
            '3h' : 10800,
            '6h' : 21600,
            '12h': 43200,
            '1d' : 86400,
            '2d' : 172800}

    def all_metrics(self):
        '''
        Get the list of all the metrics that the prometheus host has
        '''
        if not self._all_metrics:
            response = requests.get('{0}/api/v1/label/__name__/values'.format(self.url),
                                    verify=False, # Disable ssl certificate verification temporarily
                                    headers=self.headers)
            if DEBUG:
                print("Headers -> ",self.headers)
                print("URL => ", response.url)
            if response.status_code == 200:
                self._all_metrics = response.json()['data']
            else:
                raise Exception("HTTP Status Code {} {} ({})".format(
                    response.status_code,
                    requests.status_codes._codes[response.status_code][0],
                    response.content
                ))
        return self._all_metrics

    def get_metric(self, name, chunks=None, data_size=None):
        if chunks:
            if str(chunks) in self.DATA_CHUNK_SIZE_LIST:
                self.data_chunk_size = str(chunks)
                pass
            else:
                print("Invalid Chunk Size, using default value: {}".format(self.data_chunk_size))
            pass
        if data_size:
            if str(data_size) in self.DATA_CHUNK_SIZE_LIST:
                self.stored_data_range = str(data_size)
                pass
            else:
                print("Invalid Data Size, using default value: {}".format(self.stored_data_range))
            pass

        if name not in self.all_metrics():
            raise Exception("{} is not a valid metric".format(name))
        elif DEBUG:
            print("Metric is valid.")

        # num_chunks = 1
        num_chunks = int(self.DATA_CHUNK_SIZE_LIST[self.stored_data_range]/self.DATA_CHUNK_SIZE_LIST[self.data_chunk_size]) # Calculate the number of chunks using total data size and chunk size.
        metrics = self.get_metrics_from_prom(name, num_chunks)
        if metrics:
            return metrics

    def get_metrics_from_prom(self, name, chunks):
        if name not in self.all_metrics():
            raise Exception("{} is not a valid metric".format(name))

        # start = self.start_time.timestamp()
        end_timestamp = self.end_time.timestamp()
        chunk_size = self.DATA_CHUNK_SIZE_LIST[self.data_chunk_size]
        start = end_timestamp - self.DATA_CHUNK_SIZE_LIST[self.stored_data_range] + chunk_size
        data = []
        for i in range(chunks):
            # gc.collect() # Garbage collect to save Memory
            if DEBUG:
                print("Getting chunk: ", i)
                print("Start Time: ",datetime.datetime.fromtimestamp(start))

            tries = 0
            while tries < MAX_REQUEST_RETRIES:  # Retry code in case of errors
                response = requests.get('{0}/api/v1/query'.format(self.url),    # using the query API to get raw data
                                        params={'query': name+'['+self.data_chunk_size+']',
                                                'time': start
                                                },
                                        verify=False, # Disable ssl certificate verification temporarily
                                        headers=self.headers)
                if DEBUG:
                    print(response.url)
                    pass

                tries+=1
                if response.status_code == 200:
                    data += response.json()['data']['result']

                    if DEBUG:
                        # print("Size of recent chunk = ",getsizeof(data))
                        # print(data)
                        print(datetime.datetime.fromtimestamp(response.json()['data']['result'][0]['values'][0][0]))
                        print(datetime.datetime.fromtimestamp(response.json()['data']['result'][0]['values'][-1][0]))
                        pass

                    del response
                    tries = MAX_REQUEST_RETRIES
                elif response.status_code == 504:
                    if tries >= MAX_REQUEST_RETRIES:
                        self.connection_errors_count+=1
                        return False
                    else:
                        print("Retry Count: ",tries)
                        time.sleep(CONNECTION_RETRY_WAIT_TIME)    # Wait for a second before making a new request
                else:
                    if tries >= MAX_REQUEST_RETRIES:
                        self.connection_errors_count+=1
                        raise Exception("HTTP Status Code {} {} ({})".format(
                            response.status_code,
                            requests.status_codes._codes[response.status_code][0],
                            response.content
                        ))
                    else:
                        print("Retry Count: ",tries)
                        time.sleep(CONNECTION_RETRY_WAIT_TIME)

            start += chunk_size

        return((data))

    def get_current_metric_value(self, metric_name, label_config = None):
        data = []
        if label_config:
            label_list = [str(key+"="+ "'" + label_config[key]+ "'") for key in label_config]
            # print(label_list)
            query = metric_name + "{" + ",".join(label_list) + "}"
        else:
            query = metric_name
        response = requests.get('{0}/api/v1/query'.format(self.url),    # using the query API to get raw data
                                params={'query': query},#label_config},
                                verify=False, # Disable ssl certificate verification temporarily
                                headers=self.headers)
        data += response.json()['data']['result']
        return (json.dumps(data))
        pass

    @retry(stop_max_attempt_number=3)
    def get_metric_range_data(self, metric_name, start_time, end_time='now', chunk_size=None,label_config=None):
        data = []

        start = int(dateparser.parse(str(start_time)).timestamp())
        end = int(dateparser.parse(str(end_time)).timestamp())

        if not chunk_size:
            chunk_seconds = int(end - start)
            chunk_size = str(int(chunk_seconds/60)) + "m"
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
        return ((data))
