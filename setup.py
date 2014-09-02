from setuptools import setup, find_packages

setup(
    name="zeit.jabber",
    version='0.5.1.dev0',
    description="Jabber",
    author='Martijn Faassen, Christian Zagrodnick',
    author_email='faassen@startifact.com, cz@gocept.com',
    license='GPL 2',
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
