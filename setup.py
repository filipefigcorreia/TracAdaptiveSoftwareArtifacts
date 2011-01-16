from setuptools import setup

PACKAGE = 'TracAdaptiveArtifacts'
VERSION = '0.1'

setup(name=PACKAGE,
    version=VERSION,
    packages=['AdaptiveArtifacts'],
    entry_points={'trac.plugins': '%s = AdaptiveArtifacts.adaptive_artifacts' % PACKAGE},
    package_data={'AdaptiveArtifacts': ['htdocs/css/*.css',
                                        'htdocs/images/*.jpg',
                                        'templates/*.cs']},
)