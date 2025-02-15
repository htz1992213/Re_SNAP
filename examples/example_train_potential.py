import os
import numpy as np

from resnap.core.train_potential import PotentialTrainer

DATA_DIR = os.path.dirname(__file__)


def example_trainer():
    pt = PotentialTrainer(os.path.join(DATA_DIR, "re.mat"), "RIDGE")
    pt.cross_validation(np.array([0, 0.01, 0.1, 1]), plot_image="atom")
    pt.make_potential(DATA_DIR, alpha=0.0)


if __name__ == '__main__':
    example_trainer()
