"""Test function for projector module."""

import numpy as np

from simSPI.linear_simulator.projector import Projector


class AttrDict(dict):
    """Class to convert a dictionary to a class.

    Parameters
    ----------
    dict: dictionary

    """

    def __init__(self, *args, **kwargs):
        """Return a class with attributes equal to the input dictionary."""
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def init_data(path):
    """Load data for the test functions.

    Loads .npy file from a path and converts its config dictionary into a class

    Parameters
    ----------
    path: str

    Returns
    -------
    saved_data: dict
        loaded dictionary
    config: object
    """
    saved_data = np.load(path, allow_pickle=True).item()
    if "config_dict" in saved_data:
        config_dict = saved_data["config_dict"]
    else:
        config_dict = {}
    config = AttrDict(config_dict)
    return saved_data, config


def normalized_mse(a, b):
    """Return mean square error.

    Calclulates mean square error between two inputs normalized
    by the norm of the first input.

    Parameters
    ----------
    a: torch.Tensor
    b: torch.Tensor

    Returns
    -------
    out: torch.Tensor
        normalized mse
    """
    return (a - b).pow(2).sum().sqrt() / a.pow(2).sum().sqrt()


def test_projector():
    """Test accuracy of projector function."""
    path = "tests/data/projector_data.npy"

    saved_data, config = init_data(path)
    rot_params = saved_data["rot_params"]
    projector = Projector(config)
    projector.vol = saved_data["volume"]

    out = projector(rot_params)
    error = normalized_mse(saved_data["projector_output"], out).item()
    assert (error < 0.01) == 1
