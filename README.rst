ADS to BibDesk  :sup:`API edition`    (ads2bibdesk)
==============================================================

**ads2bibdesk** helps you add astrophysics articles listed on NASA/ADS to your `BibDesk <https://bibdesk.sourceforge.io>`_ database using the *new* `ADS Developer API <http://adsabs.github.io/help/api/>`_.

The program is loosely based on the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ from J. Sick et al.
*However*, the query is handled with a python client for the ADS API (`ads <http://ads.readthedocs.io>`_, maintained by A. Casey). 
Obsolete codes were replaced in favor of newer built-in Python modules with a simplified code structure. 
The MacOS workflow and app building process were updated.
The project packaging now follows the new PyPA `guideline <https://packaging.python.org/tutorials/packaging-projects>`_. 

Due to the API usage, **ads2bibdesk** requires the user to specify a personal API key (i.e., token), per the new NASA/ADS policy. 
The API key can be written into your **ads2bibdesk** preference file ``~/.ads/ads2bibdesk.cfg``.
Following the Python/ads package's instruction, one can also save the key to ``~/.ads/dev_key`` or as an environment variable named ``ADS_DEV_KEY``.


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

**ads2bibdesk** accepts two kinds of article identifier at this moment

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
* BibDesk (>=1.6.22)

While the program might work on slightly older software versions, I have no clear plan to improve the backward compatibility.
Considering that Python 2.7 will be deprecated soon and Python 3.7 may come with MacOS 10.15 by default, the decision may be appropriate,
and will reduce the required maintenance/development efforts in longer-term.
On my working machine, I have Python 3.7 from MacPorts as default::

    sudo port select pip pip37        
    sudo port select python python37
    sudo port select ipython py37-ipython
    
Status and Plan
==============================

The current approach is to start the development from a relatively clean-sheet codebase. The following functions have *already* been implemented:

- query the article metadata (title, abstract, BibTeX, etc.) with the new API by article identifiers (no more in-house ADS/arxiv HTML parsing functions)
- download article PDFs using the new ADS gateway links
- use an on-campus ``ssh`` proxy machine to download PDFs behind the journal paywall
- add/update the BibDesk database and attach downloaded PDFs (largely borrowing the `AppleScript <https://en.wikipedia.org/wiki/AppleScript>`_ method from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_)

Some other improvements from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ are:

- clean up the dependency requirements (let setup.py do the check)
- replace obsolete Python syntax/functions/modules with newer ones, e.g. optparser->argparser, f-string formatting, and use configparser()
- The MacOS Automator workflow is running the installed console script rather than an embedded Python program (this is a necessary workaround since Python 3 is not shipped as default yet)

Many features from the original `ads_bibdesk <https://github.com/jonathansick/ads_bibdesk>`_ are gone at this moment, notably, the "ingest" and "preprint-update" modes.
They can be added back in future.



   
