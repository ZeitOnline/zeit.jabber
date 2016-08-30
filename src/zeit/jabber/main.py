import ZConfig
import pkg_resources
import xmlrpclib
import zeit.jabber.jabber
import zeit.jabber.xmlrpc


def main(config_file):
    schema = ZConfig.loadSchemaFile(pkg_resources.resource_stream(
        __name__, 'schema.xml'))
    conf, handler = ZConfig.loadConfigFile(schema, open(config_file))
    conf.eventlog.startup()

    cms = xmlrpclib.ServerProxy(conf.cms.url)
    methods = tuple(method.strip() for method in conf.cms.methods.split())
    notifier = zeit.jabber.xmlrpc.Notifier(cms, methods)

    reader = zeit.jabber.jabber.Reader(
        lambda: zeit.jabber.jabber.get_jabber_client(
            conf.jabber.user, conf.jabber.password, conf.jabber.group),
        notifier, conf.jabber.ignore)

    while True:
        reader.process()
        notifier.process()
