# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

import ZConfig
import pkg_resources
import xmlrpclib
import zeit.jabber.connect


def main(config_file):
    schema = ZConfig.loadSchemaFile(pkg_resources.resource_stream(
        __name__, 'schema.xml'))
    conf, handler = ZConfig.loadConfigFile(schema, open(config_file))
    conf.eventlog.startup()
    cms = xmlrpclib.ServerProxy(conf.cms.url)
    methods = tuple(method.strip() for method in conf.cms.methods.split())

    def jabber_client_factory():
        return zeit.jabber.connect.get_jabber_client(
            conf.jabber.user, conf.jabber.password, conf.jabber.group)
    zeit.jabber.connect.main_loop(
        cms, methods, jabber_client_factory, conf.jabber.ignore)
