from setuptools import setup, find_packages


setup(
    name="zeit.jabber",
    version='1.3.5.dev0',
    description="XMPP client",
    author='Martijn Faassen, gocept, Zeit Online',
    author_email='zon-backend@zeit.de',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'sleekxmpp',
        'zope.dottedname',
        'six',
    ],
    entry_points="""
    [console_scripts]
    zeit-jabber-client=zeit.jabber.main:main
    """,
)
