from .baseflatliner import BaseFlatliner
from dataclasses import dataclass

from cachetools import LRUCache

class StdDevVersion(BaseFlatliner):
    def __init__(self, max_cache_size: int = 500):
        super().__init__()

        self.versions = LRUCache(maxsize=max_cache_size)

    def on_next(self, x):
        """ update std dev for version
        """

        # grab the resource name and the version id
        resource = x.resource
        version_id = x.version
        value = x.std_dev

        # if version_id is not present add it as an empty dictionary
        if version_id not in self.versions:
            self.versions[version_id] = dict()

        # if the resource hasen't been seen before, do std_dev initilization
        if resource not in self.versions[version_id]:
            self.versions[version_id][resource] = self.calculate_version_std(value, resource, version_id)

        # if the resource exists, grab the last entry for that cluster, resource pair.
        # set the new value to the updated values.
        else:
            previous = self.versions[version_id][resource]
            self.versions[version_id][resource] = self.calculate_version_std(value, resource,
                                                                             version_id, previous)

        self.publish(self.versions[version_id][resource])



    def calculate_version_std(self, value, resource, version, previous=None):
        # TODO: chnage from avg std to actual std for all availble resources in clusters with shared versions.
        if previous:
            count = previous.count + 1
            total = previous.total + value
            version_std_dev = total/count

        else:
            # initilize version std_dev with output of first cluster
            version_std_dev = value
            count = 1
            total = version_std_dev

        state = self.State()
        state.version = version
        state.resource = resource
        state.avg_std_dev = version_std_dev
        state.count = count
        state.total = total

        return state


    @dataclass
    class State:

        resource: str = ""
        avg_std_dev: float = 0.0
        total: float = 0.0
        count: float = 0.0
        version: str = ""
