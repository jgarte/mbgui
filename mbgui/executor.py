import collections
import concurrent.futures
import threading
import typing

import PySide6.QtCore


class Executor(PySide6.QtCore.QObject):

    def __init__(self):
        super().__init__()
        self._executor = concurrent.futures.ThreadPoolExecutor()
        self._call_main_queue = collections.deque()
        self._call_main_lock = threading.Lock()

    def call_main(self,
                  fn: typing.Callable,
                  *args):
        with self._call_main_lock:
            self._call_main_queue.append((fn, args))

        PySide6.QtCore.QMetaObject.invokeMethod(
            self, "_on_main_call", PySide6.QtCore.Qt.QueuedConnection)

    def call_worker(self,
                    fn: typing.Callable,
                    *args,
                    done_cb: typing.Callable = None,
                    ) -> concurrent.futures.Future:
        future = self._executor.submit(fn, *args)

        if done_cb:
            future.add_done_callback(
                lambda f: self.call_main(done_cb, f.result()))

        return future

    @PySide6.QtCore.Slot()
    def _on_main_call(self):
        with self._call_main_lock:
            if not self._call_main_queue:
                return

            queue = self._call_main_queue
            self._call_main_queue = collections.deque()

        for fn, args in queue:
            fn(*args)
