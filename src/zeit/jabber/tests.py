import unittest
import xmpp
import zeit.jabber.jabber
import zeit.jabber.xmlrpc


class MockRPC(object):

    exception = None

    def __init__(self):
        self.invalidated = []
        self.solr = []
        self.testing_method_log = []

    def invalidate(self, uid):
        if self.exception is not None:
            raise self.exception
        self.invalidated.append(uid)

    def update_solr(self, uid):
        self.solr.append(uid)

    def testing_method(self, uid):
        self.testing_method_log.append(uid)


class NotifierTest(unittest.TestCase):

    def setUp(self):
        self.cms = MockRPC()
        self.notifier = zeit.jabber.xmlrpc.Notifier(
            self.cms, methods=('invalidate', 'update_solr', 'testing_method'))

    def test_simple_pull(self):
        self.notifier.queue.add('foo')
        self.notifier.process()
        self.assertEquals(['foo'], self.cms.invalidated)
        self.assertEquals(['foo'], self.cms.solr)
        self.assertEquals(['foo'], self.cms.testing_method_log)

    def test_process_empties_queue_completely(self):
        self.notifier.queue.add('foo')
        self.notifier.queue.add('bar')
        self.notifier.process()
        self.assertEquals(['bar', 'foo'], sorted(self.cms.invalidated))

    def test_errors_stay_in_queue(self):
        self.notifier.queue.add('foo')
        self.notifier.queue.add('bar')
        self.cms.exception = Exception()
        self.notifier.process()
        self.assertEquals(['bar', 'foo'], sorted(self.notifier.queue))

    def test_after_max_retries_errors_are_removed_from_queue(self):
        self.notifier.queue.add('foo')
        self.cms.exception = Exception()
        self.notifier.MAX_RETRIES = 1
        self.notifier.process()
        self.notifier.process()
        self.assertEqual(set(), self.notifier.queue)

    def test_exit_on_systemexit_and_keyboardinterrupt(self):
        for exc in (SystemExit, KeyboardInterrupt):
            self.notifier.queue.add('foo')
            self.cms.exception = exc()
            self.assertRaises(exc, self.notifier.process)


class MockJabberClient(object):

    messages = []
    return_in_one_step = 100
    connected = True

    def RegisterHandler(self, type_, callback):
        self.handler = callback

    def Process(self, timeout=0):
        processed = 0
        while self.messages:
            try:
                self.handler(None, self.messages.pop(0))
            except xmpp.NodeProcessed:
                pass
            else:
                raise AssertionError("NodeProcessed not raised.")
            processed += 1
            if processed >= self.return_in_one_step:
                break
        return processed or '0'

    def isConnected(self):
        return self.connected


class JabberData(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __getattr__(self, name):
        if not name.startswith('get'):
            raise AttributeError(name)
        name = name[3:].lower()
        if name == 'from':
            name = 'from_'
        return lambda: getattr(self, name)


class ReaderTest(unittest.TestCase):

    def setUp(self):
        self.client = type('Mock', (MockJabberClient,), {})
        self.queue = set()
        self.reader = zeit.jabber.jabber.Reader(self.client, self.queue.add)

    def message(self, path, from_='cms-backend', prefix=None):
        if prefix is None:
            prefix = 'Resource changed: /cms/work/'
        return JabberData(
            from_=JabberData(resource=from_),
            body=prefix + path)

    def test_message_handler_adds_to_queue(self):
        self.client.messages.append(self.message('foo/bar'))
        self.reader.process()
        self.assertEquals(
            ['http://xml.zeit.de/foo/bar'], list(self.queue))

    def test_multiple_messages_are_added_in_one_go(self):
        self.client.messages.append(self.message('foo'))
        self.client.messages.append(self.message('bar'))
        self.client.messages.append(self.message('baz'))
        self.reader.process()
        self.assertEquals([
            'http://xml.zeit.de/bar',
            'http://xml.zeit.de/baz',
            'http://xml.zeit.de/foo'],
            sorted(list(self.queue)))

    def test_multiple_messages_are_added_in_one_go_even_if_interruped(self):
        self.client.return_in_one_step = 1
        self.client.messages.append(self.message('foo'))
        self.client.messages.append(self.message('bar'))
        self.client.messages.append(self.message('baz'))
        self.reader.process()
        self.assertEquals([
            'http://xml.zeit.de/bar',
            'http://xml.zeit.de/baz',
            'http://xml.zeit.de/foo'],
            sorted(list(self.queue)))

    def test_only_cms_work_is_added(self):
        self.client.messages.append(self.message('foo', prefix='blah'))
        self.reader.process()
        self.assertEquals([], list(self.queue))

    def test_only_cms_backend_is_added(self):
        self.client.messages.append(self.message('foo', from_='somebody-else'))
        self.reader.process()
        self.assertEquals([], list(self.queue))

    def test_disconnect(self):
        self.client.messages.append(self.message('foo'))
        self.reader.client_disconnected_sleep = 0
        self.client.connected = False
        self.reader.process()
        self.assertEquals([], list(self.queue))
        self.client.connected = True
        self.reader.process()
        self.assertEquals(
            ['http://xml.zeit.de/foo'], list(self.queue))

    def test_ignore_list(self):
        self.reader = zeit.jabber.jabber.Reader(
            self.client, self.queue.add, ['/cms/work/foo'])
        self.client.messages.append(self.message('foo'))
        self.client.messages.append(self.message('bar'))
        self.reader.process()
        self.assertEquals(['http://xml.zeit.de/bar'], sorted(list(self.queue)))
