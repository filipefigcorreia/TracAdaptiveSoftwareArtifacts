from setuptools import setup, find_packages

PACKAGE = 'AdaptiveArtifacts'
VERSION = '0.2'

setup(name=PACKAGE,
    version=VERSION,
    author='Filipe Correia',
    author_email='filipe dot correia at fe dot up dot pt',
    long_description="""
      This Trac plugin allows to create information following an arbitrary structure, that can emerge during a project's lifetime, rather than having to be established at installation/configuration time.
      """,
    packages=find_packages(exclude=['*.tests']),
    entry_points={
        'trac.plugins': [
            '%s = AdaptiveArtifacts' % PACKAGE,
            '%s.setup = AdaptiveArtifacts.persistence.db' % PACKAGE,
        ]
    },
    package_data={'AdaptiveArtifacts': ['htdocs/css/*.css',
                                        'htdocs/js/*',
                                        'htdocs/images/*.jpg',
                                        'templates/*.html']},
)
