from .baseflatliner import BaseFlatliner


class StdDevVersion(BaseFlatliner):
    def __init__(self):
        super().__init__()

    def on_next(self, x):
        """ update std dev for version
        """

        # print(f"got {x}")
        std_dev = x

        self.publish(std_dev)
