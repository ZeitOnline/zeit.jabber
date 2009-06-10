import os
import sys
import threading
import time
import xmlrpclib
import xmpp


cms = xmlrpclib.ServerProxy('http://admin:admin@localhost:8080/++skin++cms/')
invalidate = set()


class Notifier(object):

    def __init__(self, cms, queue):
        super(Notifier, self).__init__()
        self.cms = cms
        self.queue = queue

    def process(self):
        while self.queue:
            uid = self.queue.pop()
            self.cms.invalidate(uid)


class Reader(object):

    prefix = 'Resource changed: /cms/work/'

    def __init__(self, jabber_client, queue):
        self.client = jabber_client
        self.queue = queue
        self.client.RegisterHandler('message', self.message_handler)


    def message_handler(self, connection, message):
        if message.getFrom().getResource() != 'cms-backend':
            return
        body = message.getBody()
        if not body.startswith(self.prefix):
            return

        uid = 'http://xml.zeit.de/' + body[len(self.prefix):]
        self.queue.add(uid)
        raise xmpp.NodeProcessed

    def process(self):
        # When there are messages processed, it is likely there will be more.
        # Therefore we loop until there was nothing processed
        while True:
            result = self.client.Process(0.1)
            if not isinstance(result, int):
                # Disconnected or nothing processed
                # XXX what else should we do here?
                break

def main(user, password, group):
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

    queue = set()
    notifier = Notifier(cms, queue)
    reader = Reader(client, queue)

    while True:
        reader.process()
        notifier.process()
