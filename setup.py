from setuptools import setup

PACKAGE = 'TracAdaptiveArtifacts'
VERSION = '0.1'

setup(name=PACKAGE,
    version=VERSION,
    author='Filipe Correia',
    author_email='filipe dot correia at fe dot up dot pt',
    long_description="""
      This Trac plugin allows to create entities following an arbitrary structure, improving developers' expressiveness.
      """,
    packages=['AdaptiveArtifacts'],
    entry_points={'trac.plugins': '%s = AdaptiveArtifacts' % PACKAGE},
    package_data={'AdaptiveArtifacts': ['htdocs/css/*.css',
                                        'htdocs/js/*.js',
                                        'htdocs/images/*.jpg',
                                        'templates/*.cs']},
)
