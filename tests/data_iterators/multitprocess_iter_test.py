import logging
import numpy as np
import pandas as pd

import time

from package import set_logger_level as set_ll_kf
from package import set_logger_name as set_nm_kf

root_logger = logging.getLogger(__name__)
root_logger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
root_logger.addHandler(consoleHandler)

set_ll_kf(logging.INFO)
set_nm_kf(__name__)


from package.data_iterators.iterators.multiprocess_iterator import MultiProcessIterator
from package.data_iterators.samplers.ohc_balancer import OHCBalancer

from package.data_iterators.preprocessors.base_preprocessor import SlowZeroArrayReader
from package.data_iterators.preprocessors.base_preprocessor import IdentityPreprocessor
from package.routines.data_structure_routines import merge_dicts

if __name__ == '__main__':

    labels_data = np.repeat(np.arange(6), axis=0, repeats=1000)
    labels_data = pd.get_dummies(labels_data).values.astype(float)
    balancer = OHCBalancer(data=labels_data, raise_on_end=True)

    data_proc = {
        'data': SlowZeroArrayReader(name='data', shape=(1000, 1000), dtype=float)
    }

    label_proc = {
        'label': IdentityPreprocessor(name='label', shape=(6,))
    }

    iter_train = MultiProcessIterator(
        balancer=balancer, data={'data': labels_data, 'label': labels_data},
        preprocessors=merge_dicts(data_proc, label_proc), use_shared=False,
        batch_size=32,
        num_processes=6,
        max_tasks=500,
        max_results=500
    )

    start = time.time()

    for num, batch in enumerate(iter_train):
        if num % 10 == 0:
            print(time.time() - start)
            start = time.time()
        else:
            pass
