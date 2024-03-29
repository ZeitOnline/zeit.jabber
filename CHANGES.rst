zeit.jabber changes
===================

.. towncrier release notes start


1.5.0 (2023-07-26)
------------------

- MAINT: Switch to PEP420 namespace packages


1.4.0 (2022-04-14)
------------------

- ZO-856: Replace sleekxmpp with its successor slixmpp


1.3.5 (2021-10-04)
------------------

- BEM-70: Remove py2-isms


1.3.4 (2020-09-30)
------------------

- BUG-1281: Start jabber client in its own thread instead of blocking
  the main thread


1.3.3 (2020-09-18)
------------------

- BUG-1281: Fix error/retry handling (had been broken since 1.3.0)


1.3.2 (2020-03-16)
------------------

- ZON-5688: More py2 compat


1.3.1 (2020-03-16)
------------------

- ZON-5688: Fix py2 compat


1.3.0 (2020-03-16)
------------------

- ZON-5688: Replace xmpppy with SleekXmpp


1.2.0 (2017-11-02)
------------------

- BUG-800: Support selecting several different entries


1.1.0 (2017-09-04)
------------------

- BUG-773: Support ignoring everything but `/yyyy` entries


1.0.0 (2016-09-02)
------------------

- ZON-3306: Switch to ini file instead of ZConfig, make target configurable


0.5.1 (2015-04-17)
------------------

- Log retries only with warning, not error.


0.5.0 (2014-09-02)
------------------

- Give up processing after 3 retries (VIV-458).


0.4.1 (2010-07-01)
------------------

- Indicate that messages got processed. This hopefully causes the invalidator
  to not use 100% CPU time. (#7568)


0.4.0 (2010-06-03)
------------------

- Using versions from the ZTK.
- Added configuration option 'ignore' (which is a regexp and can be given
  multiple times) to ignore messages based on their contents (#5620).

0.3 (2009-08-08)
----------------

- Make the methods called on the CMS configurable.

0.2 (2009-07-28)
----------------

- Notifing CMS to reindex solr (#5520).

0.1 (2009-06-15)
----------------

- first release
