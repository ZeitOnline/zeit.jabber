import os
import sys
import logging
import threading
import time
import xmlrpclib
import xmpp


log = logging.getLogger(__name__)


class Notifier(object):

    def __init__(self, cms, queue):
        super(Notifier, self).__init__()
        self.cms = cms
        self.queue = queue

    def process(self):
        errors = []
        while self.queue:
            uid = self.queue.pop()
            log.debug('Invalidating %s' % uid)
            try:
                self.cms.invalidate(uid)
            except (SystemExit, KeyboardInterrupt), e:
                raise
            except:
                log.error("Error while invalidating, trying again lagter.",
                          exc_info=True)
                errors.append(uid)
            else:
                log.info('Invalidated %s' % uid)
        self.queue.update(errors)



class Reader(object):

    prefix = 'Resource changed: /cms/work/'

    def __init__(self, jabber_client, queue):
        self.client = jabber_client
        self.queue = queue
        self.client.RegisterHandler('message', self.message_handler)


    def message_handler(self, connection, message):
        from_ = message.getFrom().getResource()
        body = message.getBody()
        log.debug('Received message [%s] %s' % (from_, body))
        if from_ != 'cms-backend' or not body.startswith(self.prefix):
            log.debug('Ignored message')
            return
        uid = 'http://xml.zeit.de/' + body[len(self.prefix):]
        self.queue.add(uid)
        log.info('Scheduled for invalidation: %s' % uid)
        raise xmpp.NodeProcessed

    def process(self):
        # When there are messages processed, it is likely there will be more.
        # Therefore we loop until there was nothing processed
        while True:
            result = self.client.Process(10)
            if not isinstance(result, int):
                # Disconnected or nothing processed
                # XXX what else should we do here?
                break


def get_jabber_client(user, password, group):
    log.info("Connecting to jabber server as %s" % user)
    jid = xmpp.protocol.JID(user)
    client = xmpp.Client(jid.getDomain(), debug=())
    con = client.connect()
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


def main_loop(cms, jabber_client):
    queue = set()
    notifier = Notifier(cms, queue)
    reader = Reader(jabber_client, queue)

    while True:
        reader.process()
        notifier.process()
