from .baseflatliner import BaseFlatliner
from dataclasses import dataclass


class StdDevVersion(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.versions = dict()

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


    @staticmethod
    def calculate_version_std(value, resource, version, previous = None):
        #TODO: chnage from avg std to actual std for all availble resources in clusters with shared versions.
        if previous:
            count = previous.count + 1
            total = previous.total + value
            version_std_dev = total/count

        else:
            # initilize version std_dev with output of first cluster
            version_std_dev = value
            count = 1
            total = version_std_dev

        data = STD_VERSION_DATA()
        data.version = version
        data.resource = resource
        data.avg_std_dev = version_std_dev
        data.count = count
        data.total = total

        return data


@dataclass
class STD_VERSION_DATA:

    resource: str = ""
    avg_std_dev: float = 0.0
    total:float = 0.0
    count:float = 0.0
    version:str = ""
