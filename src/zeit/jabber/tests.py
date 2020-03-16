import sys
import unittest
import zeit.jabber.jabber
import zeit.jabber.xmlrpc

if sys.version_info < (3, 0):
    import Queue
else:
    import queue as Queue


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
        self.notifier.queue.put('foo')
        self.notifier.process()
        self.assertEqual(['foo'], self.cms.invalidated)
        self.assertEqual(['foo'], self.cms.solr)
        self.assertEqual(['foo'], self.cms.testing_method_log)

    def test_process_empties_queue_completely(self):
        self.notifier.queue.put('foo')
        self.notifier.queue.put('bar')
        self.notifier.process()
        self.assertEqual(['bar', 'foo'], sorted(self.cms.invalidated))

    def test_errors_stay_in_queue(self):
        self.notifier.queue.put('foo')
        self.notifier.queue.put('bar')
        self.cms.exception = Exception()
        self.notifier.process()

        queue = []

        while self.notifier.queue.qsize() > 0:
            queue.append(self.notifier.queue.get())

        self.assertEqual(['bar', 'foo'], sorted(queue))

    def test_after_max_retries_errors_are_removed_from_queue(self):
        self.notifier.queue.put('foo')
        self.cms.exception = Exception()
        self.notifier.MAX_RETRIES = 1
        self.notifier.process()
        self.notifier.process()
        self.assertEqual(0, self.notifier.queue.qsize())

    def test_exit_on_systemexit_and_keyboardinterrupt(self):
        for exc in (SystemExit, KeyboardInterrupt):
            self.notifier.queue.put('foo')
            self.cms.exception = exc()
            self.assertRaises(exc, self.notifier.process)


class MockMessage:
    resource = ''


class ReaderTest(unittest.TestCase):

    def setUp(self):
        self.queue = Queue.Queue()
        zeit.jabber.jabber.JabberClient.connect_client = lambda a: None
        self.client = zeit.jabber.jabber.JabberClient(
            '', '', '', self.queue.put)

    def test_message_handler_adds_to_queue(self):
        prefix = 'Resource changed: /cms/work/'
        from_ = 'cms-backend'

        m = MockMessage()
        m.resource = from_

        result = self.client.muc_message({
            'from': m,
            'mucnick': from_,
            'body': prefix + 'foo/bar'
        })

        self.assertIsNone(result)
        self.assertEqual(1, self.queue.qsize())

        queue = []

        while self.queue.qsize() > 0:
            queue.append(self.queue.get())

        self.assertEqual(
            ['http://xml.zeit.de/foo/bar'], list(queue))

    def test_only_cms_work_is_added(self):
        prefix = 'blah'
        from_ = 'cms-backend'

        m = MockMessage()
        m.resource = from_

        result = self.client.muc_message({
            'from': m,
            'mucnick': 'nick',
            'body': prefix + 'foo/bar'
        })

        self.assertEqual(result, 'wrong format')

    def test_only_cms_backend_is_added(self):
        prefix = 'blah'
        from_ = 'somebody-else'

        m = MockMessage()
        m.resource = from_

        result = self.client.muc_message({
            'from': m,
            'mucnick': 'nick',
            'body': prefix + 'foo/bar'
        })

        self.assertEqual(result, 'wrong format')

    def test_ignore_list(self):
        self.client = zeit.jabber.jabber.JabberClient(
            '', '', '', self.queue.put, ignore=['/cms/work/foo'])

        prefix = 'Resource changed: /cms/work/'
        from_ = 'cms-backend'

        m = MockMessage()
        m.resource = from_

        result = self.client.muc_message({
            'from': m,
            'mucnick': 'nick',
            'body': prefix + 'foo'
        })

        self.assertEqual(result, 'ignored')

    def test_ignore_list_negation(self):
        self.client = zeit.jabber.jabber.JabberClient(
            '', '', '', self.queue.put, ignore=['!/cms/work/([0-9]+)'])

        prefix = 'Resource changed: /cms/work/'
        from_ = 'cms-backend'

        m = MockMessage()
        m.resource = from_

        result = self.client.muc_message({
            'from': m,
            'mucnick': 'nick',
            'body': prefix + 'foo'
        })

        self.assertEqual(result, 'ignored')

        result = self.client.muc_message({
            'from': m,
            'mucnick': 'nick',
            'body': prefix + '2017/08/bar'
        })

        self.assertIsNone(result)
        self.assertEqual(1, self.queue.qsize())

        queue = []

        while self.queue.qsize() > 0:
            queue.append(self.queue.get())

        self.assertEqual(['http://xml.zeit.de/2017/08/bar'], sorted(queue))

    def test_ignore_list_select(self):
        self.client = zeit.jabber.jabber.JabberClient(
            '', '', '', self.queue.put, select=['/cms/work/([0-9]+)'])

        prefix = 'Resource changed: /cms/work/'
        from_ = 'cms-backend'

        m = MockMessage()
        m.resource = from_

        result = self.client.muc_message({
            'from': m,
            'mucnick': 'nick',
            'body': prefix + 'foo'
        })

        self.assertEqual(result, 'no match')

        result = self.client.muc_message({
            'from': m,
            'mucnick': 'nick',
            'body': prefix + '2017/08/bar'
        })

        self.assertIsNone(result)
        self.assertEqual(1, self.queue.qsize())

        queue = []

        while self.queue.qsize() > 0:
            queue.append(self.queue.get())

        self.assertEqual(['http://xml.zeit.de/2017/08/bar'], sorted(queue))
