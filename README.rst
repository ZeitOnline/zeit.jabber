===========
zeit.jabber
===========

Unser DAV-Server verwendet als Event-Queue einen Jabber-Chatraum, wo er
Nachrichten über geänderte Ressourcenpfade hinpostet (das Nachrichtenformat ist
``Resource changed: /cms/work/...``).

zeit.jabber stellt einen Jabber-Client zur Verfügung, der aus diesen
Jabber-Nachrichten die uniqueId ``http://xml.zeit.de/...`` extrahiert, und dann
eine konfigurierbare Aktion auslöst. Die Standard-Aktion ist ein XML-RPC Aufruf
ans vivi, um den DAV-Cache zu invalidieren und Solr zu reindizieren.

Starten mit: ``zeit-jabber-client config.ini``.


Konfiguration
=============

Der ``jabber``-Abschnitt muss Benutzer, Passwort und Chatraum angegeben, sowie
als ``target``, welche Aktion ausgelöst werden soll (das ist der Name eines
weitere Konfigurationsabschnitts). Mit ``ignore`` kann eine Liste von Regex
angegeben werden, um bestimmte Nachrichten (d.h. vor allem Pfade) zu
ignorieren.

Der ``target``-Abschnitt muss im Schlüssel ``use`` einen Python-Dottedname
enthalten, ein Callable, das den Konfigurationsabschnitt als dict übergeben
bekommt und ein Objekt zurückgibt, das eine ``__call__(item)`` Methode
bereitstellt; diese wird von der Jabber-Komponente für jede geänderte uniqueId
aufgerufen. Optional ist eine Methode ``process()``, diese wird periodisch
aufgerufen (und kann z.B. eine Queue abarbeiten).

Außerdem kann per ``loggers`` etc. das stdlib logging konfiguriert werden.

Beispiel::

    [jabber]
    user = invalid@example.com/Public Chatrooms
    password = secret
    group = notifications@conference.example.com
    target = xmlrpc
    ignore =
        ^Resource changed: /cms/work/blogs/
        ^Resource changed: /cms/work/comments/
        ^Resource changed: /cms/work/gsitemaps/
        ^Resource changed: /cms/work/import/
        ^Resource changed: /cms/work/news-nt/
        ^Resource changed: /cms/work/news/
        ^Resource changed: /cms/work/newsticker/
        ^Resource changed: /cms/work/sport-newsticker/
        ^Resource changed: /cms/work/testing/
        ^Resource changed: /cms/work/rss/

    [xmlrpc]
    use = zeit.jabber.xmlrpc.from_config
    url = http://example.com:8081/
    methods = invalidate update_solr


    # Begin logging configuration

    [loggers]
    keys = root, zeit

    [handlers]
    keys = console

    [formatters]
    keys = generic

    [logger_root]
    level = DEBUG
    handlers = console

    [logger_zeit]
    level = INFO
    handlers =
    qualname = zeit

    [handler_console]
    class = StreamHandler
    args = (sys.stdout,)
    level = NOTSET
    formatter = generic

    [formatter_generic]
    class = zope.exceptions.log.Formatter
    format = %(asctime)s %(levelname)-5.5s %(name)s %(message)s

    # End logging configuration
