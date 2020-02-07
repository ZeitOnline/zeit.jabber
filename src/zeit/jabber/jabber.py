import logging
import re
import sleekxmpp
import sleekxmpp.xmlstream

log = logging.getLogger(__name__)


class JabberClient(sleekxmpp.ClientXMPP):

    prefix = 'Resource changed: /cms/work/'
    nick = 'cms-frontend'

    def __init__(self, user, password, group, action,
                 select=None, ignore=None):

        self.boundjid = sleekxmpp.xmlstream.JID(user)
        # self.credentials = {}
        # self.password = password
        self.action = action

        self.room = group

        sleekxmpp.ClientXMPP.__init__(self, self.boundjid, password)

        # self.features = set()

        self._select = [Matcher(x) for x in select or ['^.*$']]
        self._ignore = [Matcher(x) for x in ignore or []]

        #super(sleekxmpp.ClientXMPP, self).__init__(
        #    self.boundjid, self.password)

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("muc::%s::got_online" % self.room, self.muc_online)
        self.add_event_handler('disconnected', self.disconnected)

        self.register_plugin("xep_0030")  # Service Discovery
        self.register_plugin("xep_0045")  # Multi-User Chat
        self.register_plugin("xep_0199")  # XMPP Ping

    def disconnected(self, event):
        log.debug('jabber client disconnect')

    def start(self, event):
        self.get_roster()
        self.send_presence()

        self.plugin['xep_0045'].joinMUC(self.room, self.nick, wait=True)

    def muc_online(self, presence):
        """
        Process a presence stanza from a chat room. In this case,
        presences from users that have just come online are
        handled by sending a welcome message that includes
        the user's nickname and role in the room.
        Arguments:
            presence -- The received presence stanza. See the
                        documentation for the Presence stanza
                        to see how else it may be used.
        """
        log.debug("Got presence for %s", presence['muc']['nick'])

    def muc_message(self, msg):
        """
        IMPORTANT: Always check that a message is not from yourself,
        otherwise you will create an infinite loop responding
        to your own messages."""
        if msg['mucnick'] != self.nick:
            from_ = msg['from'].resource
            body = msg['body']

            log.debug('Received message [%s] %s', from_, body)
            if from_ != 'cms-backend' or not body.startswith(self.prefix):
                log.debug('Ignored message (wrong format)')
                return 'wrong format'

            if not self.select(body):
                log.debug('Ignored message (no match in select list)')
                return 'no match'

            if self.ignore(body):
                log.debug('Ignored message (match in ignore list)')
                return 'ignored'

            uid = 'http://xml.zeit.de/' + body[len(self.prefix):]
            self.action(uid)

            log.info('Scheduling for invalidation: %s', uid)

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


def from_config(config):
    select = [x for x in config.get('select', '').split('\n') if x]
    ignore = [x for x in config.get('ignore', '').split('\n') if x]

    username = config['user']
    password = config['password']
    room = config['group']
    action = config['queue']

    return JabberClient(username, password, room, action, select, ignore)
