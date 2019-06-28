ADS to BibDesk  :sup:`API edition`    (ads2bibdesk)
==============================================================

**ads2bibdesk** helps you add astrophysics articles listed on NASA/ADS to your `BibDesk <https://bibdesk.sourceforge.io>`_ database using the *new* `ADS Developer API <http://adsabs.github.io/help/api/>`_.

The program is loosely based on the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ from J. Sick et al.
*However*, the query is handled with a python client for the ADS API (`ads <http://ads.readthedocs.io>`_, maintained by A. Casey). 
Obsolete codes are replaced in favor of newer built-in Python modules with a simplified code structure. 
The MacOS workflow building process have been updated.
The project packaging now follows the new PyPA `guideline <https://packaging.python.org/tutorials/packaging-projects>`_. 

Due to the API usage, **ads2bibdesk** requires the user to specify a personal API key, per the new NASA/ADS policy. 
The instruction on how to obtain a key can be found on this official github repo: `adsabs-dev-api <https://github.com/adsabs/adsabs-dev-api>`_. The API key can be written into your **ads2bibdesk** preference file ``~/.ads/ads2bibdesk.cfg`` (see the template `here <https://github.com/r-xue/ads2bibdesk/blob/master/ads2bibdesk.cfg.default>`_).
Following the Python/ads package's `instruction <http://ads.readthedocs.io>`_, one can also save the key to ``~/.ads/dev_key`` or as an environment variable named ``ADS_DEV_KEY``.


* Repo: https://github.com/r-xue/ads2bibdesk
* PyPI: https://pypi.python.org/pypi/ads2bibdesk

Quickstart
============

Installation
~~~~~~~~~~~~
The command line script can be installed via::

    python3 setup.py install --user     # from a local copy
    pip3 install --user ads2bibdesk     # or, from PyPI
    pip3 install --user -e .            # or, "Editable" install

To have the MacOS `service <https://support.apple.com/guide/mac-help/use-services-in-apps-mchlp1012/10.14/mac/10.14>`_ (`workflow <https://support.apple.com/guide/automator/create-a-workflow-aut7cac58839/mac>`_) installed at the same time, run one of the following options instead::

    python3 setup.py install --user --service                       # from a local copy
    pip3 install --user --install-option="--service" ads2bibdesk    # from PyPI

Usage
~~~~~

Add or update a new article from ADS::

    ads2bibdesk "2013ARA&A..51..105C"
    ads2bibdesk "2019ApJ...873..122D"
    ads2bibdesk "1301.0371"
    ads2bibdesk "2019arXiv190404507R"
    ads2bibdesk "10.3847/1538-4357/aafd37"

**ads2bibdesk** accepts three kinds of article identifier at this moment

- ADS bibcode (e.g. ``1998ApJ...500..525S``, ``2019arXiv190404507R``)
- arXiv id (e.g. ``0911.4956``).
- doi (e.g. ``10.3847/1538-4357/aafd37``)

A full summary of **ads2bibdesk** commands is available via::
    
    ads2bibdesk --help


Compatibility and Dependency
============================

I've only tested the program on the following MacOS setup:

* MacOS (>=10.14)
* Python (>=3.7.3)
* BibDesk (>=1.7.1)

While the program likely works on slightly older software versions, I don't focus on the backward compatibility.
Considering that Python 2.7 will be deprecated at the end of 2019 and `Python will not even be shipped with MacOS 10.15 (Catalina) by Apple <https://developer.apple.com/documentation/macos_release_notes/macos_catalina_10_15_beta_2_release_notes>`_ (so the users can do whatever you want), the decision looks appropriate and will reduce the required maintenance/development efforts in longer-term.
On my working machine (Mojave), I have Python 3.7 from MacPorts as default::

    sudo port select pip pip37        
    sudo port select python python37
    sudo port select ipython py37-ipython
    
Status
==============================

The following functions have *already* been implemented in the package:

- query the article metadata (title, abstract, BibTeX, etc.) with the new API by article identifiers (no more in-house ADS/arxiv HTML parsing functions)
- download article PDFs using the ADS gateway links
- use an authorized on-campus ``ssh`` proxy machine (with your public key) to download PDFs behind the journal paywall
- add/update the BibDesk database and attach downloaded PDFs (largely borrowing the `AppleScript <https://en.wikipedia.org/wiki/AppleScript>`_ method from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_)

Other changes from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ include:

- clean up the dependency requirements (let setup.py do the check)
- replace obsolete Python syntax/functions/modules with newer ones, e.g. optparser->argparser, f-string formatting, and use configparser()
- The MacOS Automator workflow is running the installed console script rather than an embedded Python program

Some less-used features from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ are gone: notably, the "ingest" and "preprint-update" modes.
But I plan to at least add back the "preprint-update" option, by scanning/updating ``article_bibcode`` associated with arXiv). My improvement proposal can be found `here <https://github.com/r-xue/ads2bibdesk/labels/enhancement>`_.



   
