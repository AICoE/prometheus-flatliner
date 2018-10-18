from .baseflatliner import BaseFlatliner


class StdDevCluster(BaseFlatliner):
    def __init__(self):
        super().__init__()

    def on_next(self, x):
        """ update calculate std dev for cluster
        """

        print(f"got {x}")
        std_dev = 21
        self.publish(std_dev)
