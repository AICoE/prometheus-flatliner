from .baseflatliner import BaseFlatliner
import flatliners

from dataclasses import dataclass

class WeirdnessScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()

    def on_next(self, x):

        cluster_name = x.cluster
        version = x.version

        if cluster_name not in self.score:
            self.score[cluster_name] = self.State()
            self.score[cluster_name].cluster = cluster_name

        if isinstance(x, flatliners.comparisonscore.ComparisonScore.State):
            self.score[cluster_name].std_dev = float(x.std_norm)
            self.score[cluster_name].std_dev_timestamp = float(x.timestamp)
            self.score[cluster_name].std_dev_buffer = True
            self.score[cluster_name].version = version

        if self.score[cluster_name].std_dev_buffer:
            self.score[cluster_name].weirdness_score = self.score[cluster_name].std_dev
            self.publish(self.score[cluster_name])

    @dataclass
    class State:

        cluster: str = ""
        version: str = ""
        std_dev: float = 0.0
        std_dev_timestamp: float = 0.0
        weirdness_score:float = 0.0
        std_dev_buffer: bool = False

