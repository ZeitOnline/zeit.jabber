import logging
import queue
import time
import xmlrpc.client


log = logging.getLogger(__name__)


class Notifier(object):

    MAX_RETRIES = 3
    EMPTY_PAUSE = 10

    def __init__(self, cms, methods):
        super(Notifier, self).__init__()
        self.cms = cms
        self.queue = queue.Queue()
        self.methods = methods
        self.retries = {}

    def __call__(self, item):
        self.queue.put(item)

    def process(self):
        while True:
            self._process()  # So tests can run single steps

    def _process(self):
        try:
            uid = self.queue.get_nowait()
        except queue.Empty:
            for item, _retries in self.retries.items():
                self(item)
            time.sleep(self.EMPTY_PAUSE)
            return

        attempts = self.retries.get(uid, 0)
        if attempts >= self.MAX_RETRIES:
            log.error("Giving up on %s after %s retries", uid, attempts)
            del self.retries[uid]
            return

        log.debug('Invalidating %s', uid)
        try:
            for method in self.methods:
                getattr(self.cms, method)(uid)
        except Exception:
            attempts = self.retries.setdefault(uid, 0)
            self.retries[uid] = attempts + 1
            log.warning("Error while invalidating %s, trying again later.",
                        uid, exc_info=True)
        else:
            log.info('Invalidated %s', uid)


def from_config(config):
    cms = xmlrpc.client.ServerProxy(config['url'])
    methods = tuple(x.strip() for x in config['methods'].split())
    return Notifier(cms, methods)
