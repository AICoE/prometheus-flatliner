from .baseflatliner import BaseFlatliner
import flatliners

from dataclasses import dataclass

class WeirdnessScore(BaseFlatliner):
    def __init__(self):
        super().__init__()

        self.score = dict()

    def on_next(self, x):

        cluster_name = x.cluster

        if cluster_name not in self.score:
            #self.score[cluster_name] = dict()
            self.score[cluster_name] = WEIRDNESS_SCORES()
            self.score[cluster_name].cluster = cluster_name

        if isinstance(x, flatliners.corrcomparison.CORR_COMPARISON):
            self.score[cluster_name].correlation = float(x.corr_norm)
            self.score[cluster_name].correlation_timestamp = float(x.timestamp)
            self.score[cluster_name].corr_buffer = True


        if isinstance(x, flatliners.comparisonscore.STD_COMPARISON_DATA):
            self.score[cluster_name].std_dev = float(x.std_norm)
            self.score[cluster_name].std_dev_timestamp = float(x.timestamp)
            self.score[cluster_name].std_dev_buffer = True


        if self.score[cluster_name].corr_buffer and self.score[cluster_name].std_dev_buffer:
            self.score[cluster_name].weirdness_score = self.score[cluster_name].correlation \
                                            + self.score[cluster_name].std_dev

            self.publish(self.score[cluster_name])

@dataclass
class WEIRDNESS_SCORES:
    cluster: str = ""
    correlation: float = 0.0
    correlation_timestamp: float = 0.0
    std_dev: float = 0.0
    std_dev_timestamp: float = 0.0
    weirdness_score:float = 0.0
    corr_buffer: bool = False
    std_dev_buffer: bool = False

