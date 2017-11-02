import logging
import re
import time
import xmpp


log = logging.getLogger(__name__)


class Matcher(object):

    def __init__(self, regex):
        if regex.startswith('!'):
            self.negate = True
            regex = regex[1:]
        else:
            self.negate = False
        self.regex = re.compile(regex)

    def __call__(self, text):
        result = bool(self.regex.search(text))
        if self.negate:
            result = not result
        return result


class Reader(object):

    prefix = 'Resource changed: /cms/work/'
    client = None
    client_disconnected_sleep = 10

    def __init__(self, jabber_client_factory, action,
                 select=None, ignore=None):
        """
        :param jabber_client_factory: callable with no arguments to create a
          jabber client (we need to recreate it to support reconnect)
        :param queue: an object that provides an `add(item)` method,
          which we'll call for each changed uniqueId.
        """
        self.client_factory = jabber_client_factory
        self.action = action
        self._select = [Matcher(x) for x in select or ['^.*$']]
        self._ignore = [Matcher(x) for x in ignore or []]

    def get_client(self):
        if self.client is None:
            self.client = self.client_factory()
        if self.client and self.client.isConnected():
            self.client.RegisterHandler('message', self.message_handler)
        else:
            log.error("Could not connect to webdav server.")
            self.client = None
        return self.client

    def reconnect_client(self):
        self.client = None
        self.get_client()

    def message_handler(self, connection, message):
        from_ = message.getFrom().getResource()
        body = message.getBody()
        log.debug('Received message [%s] %s', from_, body)
        if from_ != 'cms-backend' or not body.startswith(self.prefix):
            log.debug('Ignored message (wrong format)')
            raise xmpp.NodeProcessed
        if not self.select(body):
            log.debug('Ignored message (no match in select list)')
            raise xmpp.NodeProcessed
        if self.ignore(body):
            log.debug('Ignored message (match in ignore list)')
            raise xmpp.NodeProcessed
        uid = 'http://xml.zeit.de/' + body[len(self.prefix):]
        self.action(uid)
        log.info('Scheduling for invalidation: %s', uid)
        raise xmpp.NodeProcessed

    def select(self, text):
        for matcher in self._select:
            if matcher(text):
                return True
        return False

    def ignore(self, text):
        for matcher in self._ignore:
            if matcher(text):
                return True
        return False

    def process(self):
        # When there are messages processed, it is likely there will be more.
        # Therefore we loop until there was nothing processed
        while True:
            client = self.get_client()
            if client is None:
                time.sleep(self.client_disconnected_sleep)
                break
            result = client.Process(10)
            if result:
                if not int(result):
                    # No message processed
                    break
            else:
                # Error
                break


def get_jabber_client(user, password, group):
    log.info("Connecting to jabber server as %s", user)
    jid = xmpp.protocol.JID(user)
    client = xmpp.Client(jid.getDomain(), debug=())
    client.connect()
    if not client.isConnected():
        return None
    auth = client.auth(jid.getNode(), password, resource=jid.getResource())
    client.sendInitPresence()
    nick_base = 'cms-frontend'
    nick = nick_base
    i = 0
    while True:
        i += 1
        group_jid = '%s/%s' % (group, nick)
        group_jid = xmpp.protocol.JID(group_jid)
        response = client.SendAndWaitForResponse(
            xmpp.dispatcher.Presence(to=group_jid))
        if not response.getError():
            break
        nick = '%s-%s' % (nick_base, i)

    log.info("Joined %s as %s", group, nick)
    return client


def from_config(config):
    select = [x for x in config.get('select', '').split('\n') if x]
    ignore = [x for x in config.get('ignore', '').split('\n') if x]
    return Reader(
        lambda: get_jabber_client(
            config['user'], config['password'], config['group']),
        config['queue'], select, ignore)
