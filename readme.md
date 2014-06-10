ASA plugin for Trac
===================

Status
------

Consider this an alpha release. I will appreciate all the feedback on the plugin, but please note that it's an early prototype. It may be vulnerable to attacks (e.g., XSS), and therefore is not advisable to make available outside firewalls.

Only tested with sqlite, but it's likely to work with other database engines, namely postgresql.

Architecture
------------

The ASA plugin makes use of the [Adaptive Object-Model](http://adaptiveobjectmodel.com/) architectural pattern and is supported by the Language Piggybacking pattern. 

Setting-up the Development Environment
--------------------------------------

**1st.** Setup a [development environment for trac](http://trac.edgewall.org/wiki/TracDev/DevelopmentEnvironmentSetup)

**2nd.** Create a test trac environment.

**3rd.** Checkout the plugin sources from the repository 

**4th.** Install the plugin:

    python setup.py develop -md /var/local/trac/anadaptiveproject/plugins

**5th.** Start *tracd* and check if you can open the newly created environment in the browser

    tracd -r --port 8000 /var/local/trac/anadaptiveproject
    
Refer to [Using tracd](http://trac.edgewall.org/wiki/TracStandalone) for further options.

**6th.** Enable the plugin on your trac environment's administration page (`Admin > Plugins`)

**7th.** Include the *adaptiveartifacts* item to the project's *trac.ini*, to add the plugin to the main navigation bar:

    [trac] 
    mainnav = wiki,adaptiveartifacts,timeline,roadmap,browser,tickets,newticket,search

**8th.** Hack, hack, hack, hack.

**9th.** Tracd should restart automatically.

Extra recommendations:
  * I strongly advise the use of [virtualenv](http://iamzed.com/2009/05/07/a-primer-on-virtualenv/);
  * Remember, contributions are more likely to be accepted quickly if accompanied by the respective unit tests.

Using The Tests
---------------

Running them:

    python -m AdaptiveArtifacts.tests.model


Running test coverage:

    coverage run -m AdaptiveArtifacts.tests.model
    coverage report -m --include=*AdaptiveArtifacts*

To get an HTML report:

    coverage html --include=*AdaptiveArtifacts*


Notes: 
  * In case you don't have coverage.py, you can install it via easy_install or pip
  * The root dir of the python modules must be findable by python (e.g., included on PYTHONPATH)


