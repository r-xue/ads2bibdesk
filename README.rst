ADS to BibDesk  :sup:`API edition`    (ads2bibdesk)
==============================================================

**ads2bibdesk** helps you add astrophysics articles listed on NASA/ADS to your `BibDesk <https://bibdesk.sourceforge.io>`_ database using the *new* `ADS Developer API <http://adsabs.github.io/help/api/>`_.

The program is loosely based on the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ from J. Sick et al.
*However*, the query is handled with a python client for the ADS API (`ads <http://ads.readthedocs.io>`_, maintained by A. Casey).
Obsolete codes are replaced in favor of newer built-in Python modules with a simplified code structure.
The macOS workflow building process have been updated.
The project packaging now follows the new PyPA `guideline <https://packaging.python.org/tutorials/packaging-projects>`_.

Due to the API usage, **ads2bibdesk** requires the user to specify a personal API key, per the new NASA/ADS policy.
The instruction on how to obtain a key can be found on this official github repo: `adsabs-dev-api <https://github.com/adsabs/adsabs-dev-api>`_.
In short, to obtain access to the ADS Developer API, one must do two things:

- `Create an account <https://ui.adsabs.harvard.edu/user/account/register>`_ and log in to the latest version of the ADS
- Push the “Generate a new key” button under `Customize Settings -> Account Settings -> API Token <https://ui.adsabs.harvard.edu/user/settings/token>`_

The API key can be written into your **ads2bibdesk** preference file ``~/.ads/ads2bibdesk.cfg`` (see the `template <https://github.com/r-xue/ads2bibdesk/blob/master/ads2bibdesk/ads2bibdesk.cfg.default>`_).
Following the Python/ads package's `instruction <http://ads.readthedocs.io>`_, one can also save the key to ``~/.ads/dev_key`` or as an environment variable named ``ADS_DEV_KEY``.

* Repo: https://github.com/r-xue/ads2bibdesk
* PyPI: https://pypi.python.org/pypi/ads2bibdesk

Credit to the contributors of the original `ads_bibdesk` 
`@jonathansick <http://github.com/jonathansick>`_ `@RuiPereira <https://github.com/RuiPereira>`_ `@keflavich <https://github.com/keflavich>`_ for their initial implementation.

Quickstart
============

Installation
~~~~~~~~~~~~
The command line script can be installed via::

    pip install --user git+https://github.com/r-xue/ads2bibdesk.git # from GitHub
    pip install --user ads2bibdesk                                  # from PyPI (likely behind the GitHub version) 
    pip install --user .                                            # from a local copy 
    pip install --user -e .                                         # from a local copy, "Editable" install

To have the macOS app and `service <https://support.apple.com/guide/mac-help/use-services-in-apps-mchlp1012/10.15/mac/10.15>`_ built at the same time, run one of the following options instead::

    pip install --user --upgrade --install-option="--service" .               # from a local copy
    pip install --user --upgrade --install-option="--service" ads2bibdesk     # from PyPI

The option "--service" will create two files ``Add to BibDesk.workflow`` and ``Add to BibDesk.app`` in ``~/Downloads/``. To install the service, click ``Add to BibDesk.workflow`` and it will be moved to ``~/Library/Services/``. For the app, just drag and drop it to any preferred location. 

Note: 

* Only Python >=3.7 is supported (see below_). 
* With the "--user" option, you must add the user-level bin directory (e.g., ``~/Library/Python/3.X/bin``) to your PATH environment variable in order to launch **ads2bibdesk**.
* Both the macOS service and app are based on the Automator `workflow <https://support.apple.com/guide/automator/create-a-workflow-aut7cac58839/mac>`_). They simply wrap around the command line program and serve as its shortcuts.
* The service shortcut will not work within some applications (e.g., Safari) on macOS >=10.14 due to new privacy and security features built in macOS (see this `issue <https://github.com/r-xue/ads2bibdesk/issues/8>`_)


Usage
~~~~~

From the Command line
^^^^^^^^^^^^^^^^^^^^^

Add or update a new article from ADS::

    ads2bibdesk "1807.04291"
    ads2bibdesk "2018ApJ...864L..11X"
    ads2bibdesk "2013ARA&A..51..105C"
    ads2bibdesk "10.3847/2041-8213/aaf872"

**ads2bibdesk** accepts three kinds of article identifier at this moment

- ADS bibcode (e.g. ``1998ApJ...500..525S``, ``2019arXiv190404507R``)
- arXiv id (e.g. ``0911.4956``).
- doi (e.g. ``10.3847/1538-4357/aafd37``)

A full summary of **ads2bibdesk** commands is available via::

    ads2bibdesk --help

From the macOS app
^^^^^^^^^^^^^^^^^^

1. Copy the article identifider to the clipboard, in any application 
2. launch ``Add to BibDesk.app``

From the macOS service
^^^^^^^^^^^^^^^^^^^^^^

1. Highligh and right-click on the article identifider
2. Choose 'Services > Add to Bibdesk' from the right-click menu

Compatibility and Dependency
============================
.. _below:

I've only tested the program on the following macOS setup:

* macOS (>=10.14)
* Python (>=3.7.3)
* BibDesk (>=1.7.1)

While the program likely works on slightly older software versions, I don't focus on the backward compatibility.
On my working machine (Catalina), I set Python 3.8 from MacPorts as default::

    sudo port install python38 py38-pip py38-ipython
    sudo port select python python38
    sudo port select ipython py38-ipython
    sudo port select pip pip38

Status
==============================

The following functions have *already* been implemented in the package:

- query the article metadata (title, abstract, BibTeX, etc.) with the new API by article identifiers (no more in-house ADS/arxiv HTML parsing functions)
- download article PDFs using the ADS gateway links
- use an authorized on-campus ``ssh`` proxy machine (with your public key) to download PDFs behind the journal paywall
- add/update the BibDesk database and attach downloaded PDFs (largely borrowing the `AppleScript <https://en.wikipedia.org/wiki/AppleScript>`_ method from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_)

Other changes from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ include:

- clean up the dependency requirements 
- replace obsolete Python syntax/functions/modules with newer ones, e.g. optparser->argparser, f-string formatting, and use configparser()
- The macOS Automator workflow is running the installed console script rather than an embedded Python program

Some less-used features from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ are gone: notably, the "ingest" and "preprint-update" modes.
But I plan to at least add back the "preprint-update" option, by scanning/updating ``article_bibcode`` associated with arXiv). My improvement proposal can be found `here <https://github.com/r-xue/ads2bibdesk/labels/enhancement>`_.
