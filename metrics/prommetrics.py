import json
import os
import sys
import dateparser
import logging

from rx import Observable

#Prometheus connection stuff
from prometheus import Prometheus

# Set up logging
_LOGGER = logging.getLogger(__name__)


class PromMetrics:
    def __init__(self, metrics_list, metric_start_datetime='1h', metric_end_datetime='now', metric_chunk_size='1h'):
        self.observable = Observable.create(self.push_metrics).publish()
        self.metrics_list = metrics_list
        self.metric_start_datetime = metric_start_datetime
        self.metric_end_datetime = metric_end_datetime
        self.metric_chunk_size = metric_chunk_size
        self.final_packet_timestamp = dict()
        self.final_packet_timestamp[0] = 0

    def subscribe(self, observer):
        self.observable.subscribe(observer)

    def connect(self):
        self.observable.connect()

    def push_metrics(self, observer):
        self.observe_prom_metrics_range(observer=observer,
                                        metrics_list=self.metrics_list,
                                        start_time=self.metric_start_datetime,
                                        end_time=self.metric_end_datetime,
                                        chunk_size=self.metric_chunk_size)

    def observe_prom_metrics_range(self, observer, metrics_list, start_time, end_time='now', chunk_size='1h'):
        # Collect credentials to connect to a prometheus instance
        prom_token = os.getenv("FLT_PROM_ACCESS_TOKEN")
        prom_url = os.getenv("FLT_PROM_URL")
        if not (prom_token or prom_url):
            sys.exit("Error: Prometheus credentials not found")
        prom = Prometheus(url=prom_url, token=prom_token)

        # Calculate chunk size to download and push to the observer at each instance
        chunk_seconds = int(round((dateparser.parse('now') - dateparser.parse(chunk_size)).total_seconds()))

        start = round(dateparser.parse(start_time).timestamp(),0)
        end = round(dateparser.parse(end_time).timestamp(),0)

        _LOGGER.info("Collecting metric data within datetime range:{0} - {1}".format(dateparser.parse(str(start)),dateparser.parse(str(end))))
        current_latest_timestamp = 0

        while start < end:     # Main loop which iterates through time-ranges to collect a chunk of data at every iteration
            chunk_end_time = start + chunk_seconds -1  # Increment the metric chunk time to collect the next chunk

            if (start+chunk_seconds) >= end:         # When the specified start-end datetime range is not divisible by the specified chunk time
                chunk_end_time = end          # Reduce the size of the last chunk to fit the specified datetime frame

            for metric_name in metrics_list:    # Loop to get a chunk of data for every metric in the list
                _LOGGER.debug("Current Chunk Info: Metric = {0}, Time range = {1} - {2}".format(metric_name,
                                                                                dateparser.parse(str(start)),
                                                                                dateparser.parse(str(chunk_end_time))))
                pkt_list = (prom.get_metric_range_data(metric_name=metric_name, start_time=start, end_time=chunk_end_time))
                _LOGGER.debug("Collected {0} packets.".format(len(pkt_list)))

                for pkt in pkt_list:        # pkt_list contains a list of data for multiple metrics, each of which is pushed to the observer.
                    # print(dateparser.parse(str(pkt['values'][0][0])), "-", dateparser.parse(str(pkt['values'][-1][0])))
                    if pkt['values'][-1][0] > current_latest_timestamp:
                        current_latest_timestamp = pkt['values'][-1][0]
                    try:
                        observer.on_next(pkt)
                    except Exception as e:
                        _LOGGER.error("{0}, while processing the following metric packet: \n{1}".format(str(e),str(pkt)))  # Check which pkt caused the exception
                        raise(e)
                self.final_packet_timestamp[metric_name] = (current_latest_timestamp)

            start += chunk_seconds
        pass
