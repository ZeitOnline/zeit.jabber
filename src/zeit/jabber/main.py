import ConfigParser
import argparse
import logging.config
import os.path
import zeit.jabber.jabber
import zope.dottedname.resolve


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Listen for uniqueIds on jabber and act on them')
    parser.add_argument(
        'configfile', help='ini file')
    options = parser.parse_args(argv)
    config = ConfigParser.ConfigParser()
    configfile = os.path.abspath(options.configfile)
    config.read(configfile)

    # Inspired by pyramid.paster.setup_logging().
    if config.has_section('loggers'):
        logging.config.fileConfig(configfile, {
            '__file__': configfile, 'here': os.path.dirname(configfile)})

    target = config.get('jabber', 'target')
    factory = zope.dottedname.resolve.resolve(config.get(target, 'use'))
    notifier = factory(dict(config.items(target)))

    jabber = dict(config.items('jabber'))
    jabber['queue'] = notifier
    reader = zeit.jabber.jabber.from_config(jabber)

    while True:
        reader.process()
        notifier.process()
