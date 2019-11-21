import logging
import six.moves.xmlrpc_client


log = logging.getLogger(__name__)


class Notifier(object):

    MAX_RETRIES = 3

    def __init__(self, cms, methods):
        super(Notifier, self).__init__()
        self.cms = cms
        self.queue = set()
        self.methods = methods
        self.retries = {}

    def __call__(self, item):
        self.queue.add(item)

    def process(self):
        errors = []
        while self.queue:
            uid = self.queue.pop()
            attempts = self.retries.get(uid, 0)
            if attempts >= self.MAX_RETRIES:
                log.error("Giving up on %s after %s retries", uid, attempts)
                del self.retries[uid]
                continue
            log.debug('Invalidating %s', uid)
            try:
                for method in self.methods:
                    getattr(self.cms, method)(uid)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                attempts = self.retries.setdefault(uid, 0)
                self.retries[uid] = attempts + 1
                log.warning("Error while invalidating %s, trying again later.",
                            uid, exc_info=True)
                errors.append(uid)
            else:
                log.info('Invalidated %s', uid)
        self.queue.update(errors)


def from_config(config):
    cms = six.moves.xmlrpc_client.ServerProxy(config['url'])
    methods = tuple(x.strip() for x in config['methods'].split())
    return Notifier(cms, methods)
