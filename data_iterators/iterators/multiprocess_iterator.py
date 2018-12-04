import multiprocessing as mp
from queue import Full, Empty
import mxnet as mx

import logging
from multiprocessing_logging import install_mp_handler

from .base_iterator import BaseIterator
from ... import ROOT_LOGGER_NAME, ROOT_LOGGER_LEVEL
logger = logging.getLogger('{}.{}'.format(ROOT_LOGGER_NAME, __name__))
logger.setLevel(ROOT_LOGGER_LEVEL)
install_mp_handler(logger=logger)


class MultiProcessIterator(BaseIterator):
    def __init__(self, num_processes, max_tasks=100, max_results=1000, *args, **kwargs):
        super(MultiProcessIterator, self).__init__(*args, **kwargs)
        self._num_processes = num_processes
        self._max_tasks = max(max_tasks, self._batch_size)
        self._max_results = max(max_results, self._batch_size)

        self._input_storage = mp.Queue(self._max_tasks)
        self._output_storage = mp.Queue(self._max_results)

        worker_func = self._make_worker_func()
        self._workers = []
        for i in range(num_processes):
            proc = mp.Process(target=worker_func,  args=(self._input_storage, self._output_storage))
            proc.daemon = True
            proc.start()
            self._workers.append(proc)
        self._continue = self.next_tasks()

    def _make_worker_func(self):
        def task_func(task_queue, result_queue):
            while True:
                result = {}
                idx, data_pack = task_queue.get()  # waiting for available task
                for key, processor in self._preprocessors.items():
                    key = key if isinstance(key, tuple) else (key,)
                    instance = {k: self._joint_storage[k][idx] for k in key}
                    result.update(processor.process(**instance))
                result_queue.put(result)

        return task_func

    def next_tasks(self, num_tasks=None):
        task_added = 0
        num_tasks = num_tasks or self._max_tasks
        while task_added < num_tasks:  # iterate until full or stop
            try:
                idx = self._balancer.next()
                data_pack = {key: self._joint_storage[key][idx] for key in self._joint_keys}

                self._input_storage.put_nowait((idx, data_pack))
                task_added += 1
            except Full:
                return True
            except StopIteration:
                return False
        return True

    def next(self):
        if self._num_batches is not None and self._num_batches == self._batch_counter:
            raise StopIteration

        data_packs = [[] for _ in self._data_keys]
        label_packs = [[] for _ in self._label_keys]
        indices_to_ret = []

        sample_num = 0

        while sample_num < self._batch_size:
            try:
                idx, data, labels = self._output_storage.get(True, 10)
                # idx - sample index, data - (num_data, ...), labels - (num_labels, ...)
                # if no exception here
                indices_to_ret.append(idx)
                for num_data, d in enumerate(data):
                    data_packs[num_data].append(d)
                for num_label, l in enumerate(labels):
                    label_packs[num_label].append(l)
                sample_num += 1
            except Empty:
                break

        self._continue = self.next_tasks() if self._continue else self._continue
        if not self._continue and len(indices_to_ret) == 0:
            raise StopIteration

        data_batched = [mx.nd.array(data_pack) for data_pack in data_packs]
        labels_batched = [mx.nd.array(label_pack) for label_pack in label_packs]

        self._batch_counter += 1
        if not self._return_indices:
            return mx.io.DataBatch(data=data_batched, label=labels_batched, pad=0)
        else:
            return mx.io.DataBatch(data=data_batched, label=labels_batched, pad=0), indices_to_ret


