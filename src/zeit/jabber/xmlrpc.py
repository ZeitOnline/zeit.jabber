import sys

import logging
import time
import xmlrpc

if sys.version_info[0] < 3:
    import Queue
else:
    import queue as Queue


log = logging.getLogger(__name__)


class Notifier(object):

    MAX_RETRIES = 3
    EMPTY_PAUSE = 10

    def __init__(self, cms, methods):
        super(Notifier, self).__init__()
        self.cms = cms
        self.queue = Queue.Queue()
        self.methods = methods
        self.retries = {}

    def __call__(self, item):
        self.queue.put(item)

    def process(self):
        errors = []
        while self.queue.qsize() > 0:
            try:
                uid = self.queue.get_nowait()
            except Queue.Empty:
                for item, retries in self.retries.items():
                    if retries == 1:
                        self(item)
                time.sleep(self.EMPTY_PAUSE)
                continue

            attempts = self.retries.get(uid, 0)
            if attempts >= self.MAX_RETRIES:
                log.error("Giving up on %s after %s retries", uid, attempts)
                del self.retries[uid]
                continue

            log.debug('Invalidating %s', uid)
            try:
                for method in self.methods:
                    getattr(self.cms, method)(uid)
            except Exception:
                attempts = self.retries.setdefault(uid, 0)
                self.retries[uid] = attempts + 1
                log.warning("Error while invalidating %s, trying again later.",
                            uid, exc_info=True)
                errors.append(uid)
            else:
                log.info('Invalidated %s', uid)

        for err_uid in errors:
            self.queue.put(err_uid)


def from_config(config):
    with xmlrpc.client.ServerProxy(config['url']) as cms:
        methods = tuple(x.strip() for x in config['methods'].split())
        return Notifier(cms, methods)
