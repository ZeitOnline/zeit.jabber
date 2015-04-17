from setuptools import setup, find_packages


setup(
    name="zeit.jabber",
    version='0.5.2.dev0',
    description="XMPP client",
    author='Martijn Faassen, gocept, Zeit Online',
    author_email='zon-backend@zeit.de',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'ZConfig',
        'setuptools',
        'xmpppy',
    ],
    entry_points="""
    [console_scripts]
    notify=zeit.jabber.main:main
    """,
)
