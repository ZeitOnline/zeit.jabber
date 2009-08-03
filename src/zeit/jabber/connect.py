import logging
import os
import sys
import threading
import time
import xmpp


log = logging.getLogger(__name__)


class Notifier(object):

    def __init__(self, cms, queue, methods):
        super(Notifier, self).__init__()
        self.cms = cms
        self.queue = queue
        self.methods = methods

    def process(self):
        errors = []
        while self.queue:
            uid = self.queue.pop()
            log.debug('Invalidating %s' % uid)
            try:
                for method in self.methods:
                    getattr(self.cms, method)(uid)
            except (SystemExit, KeyboardInterrupt), e:
                raise
            except:
                log.error("Error while invalidating, trying again later.",
                          exc_info=True)
                errors.append(uid)
            else:
                log.info('Invalidated %s' % uid)
        self.queue.update(errors)



class Reader(object):

    prefix = 'Resource changed: /cms/work/'
    client = None
    client_disconnected_sleep = 10

    def __init__(self, jabber_client_factory, queue):
        self.client_factory = jabber_client_factory
        self.queue = queue

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
        log.debug('Received message [%s] %s' % (from_, body))
        if from_ != 'cms-backend' or not body.startswith(self.prefix):
            log.debug('Ignored message')
            return
        uid = 'http://xml.zeit.de/' + body[len(self.prefix):]
        self.queue.add(uid)
        log.info('Scheduling for invalidation: %s' % uid)
        raise xmpp.NodeProcessed

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
    log.info("Connecting to jabber server as %s" % user)
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

    log.info("Joined %s as %s" % (group, nick))
    return client


def main_loop(cms, methods, jabber_client_factory):
    queue = set()
    notifier = Notifier(cms, queue, methods)
    reader = Reader(jabber_client_factory, queue)

    while True:
        reader.process()
        notifier.process()
