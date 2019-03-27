'''
Rx module to filter metrics based on their version
'''
import logging
import regex as re

from .baseflatliner import BaseFlatliner

# Set up logging
_LOGGER = logging.getLogger(__name__)



class VersionFilter(BaseFlatliner):
    '''
    Rx module to filter metrics based on their version
    '''
    def __init__(self, version_regex):
        super().__init__()
        # create a regex pattern from the specified expression
        self.version_regex_pattern = re.compile(version_regex)
        _LOGGER.info("Version filter initialized with regex espression: %s", version_regex)

    def on_next(self, x):
        if self.version_regex_pattern.match(str(x["metric"]["version"])):
            # if the version matches the regex pattern publish it
            self.publish(x)
