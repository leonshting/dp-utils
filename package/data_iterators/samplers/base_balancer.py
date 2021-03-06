import numpy as np
import logging

from ... import ROOT_LOGGER_NAME, ROOT_LOGGER_LEVEL
logger = logging.getLogger('{}.{}'.format(ROOT_LOGGER_NAME, __name__))
logger.setLevel(ROOT_LOGGER_LEVEL)


class BaseBalancer(object):
    """
    Iterates through index with one by one provided iterable data
    """
    def __init__(self, data, raise_on_end=False, shuffle=True, verbose=False, *args, **kwargs):
        """
        Provides new index balancer with next method, with corresponding balancing
        :param data: iterable with indices that will be passed into processors
        :param raise_on_end: raise StopIteration when every label is visited
        :param shuffle: permute provided index
        :param verbose: whether balancer yields messages to balancer
        """
        self._shuffle = shuffle
        self._data = data
        self._raise_on_end = raise_on_end
        self._verbose = verbose

        self._reset()

    def _reset(self):
        if self._shuffle:
            self._perm = np.random.permutation(self.data_length)
        else:
            self._perm = np.arange(self.data_length, dtype=int)
        self._visited = set()

    def pre_next(self):
        if self._verbose and len(self._visited) % 100 == 0:
            logger.info("visited set length - {}".format(len(self._visited)))
        if len(self._visited) == self.data_length:
            if self._raise_on_end:
                raise StopIteration
            self.reset()

    def post_next(self):
        self._visited.add(len(self._visited))

    @property
    def visited_set(self):
        return self._visited

    @property
    def data_length(self):
        return len(self._data)

    @property
    def current_id(self):
        return len(self._visited)

    def reset(self):
        self._reset()

    def next(self):
        self.pre_next()
        ret_idx = self.current_id
        self.post_next()
        return self._perm[ret_idx]
