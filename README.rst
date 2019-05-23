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
    pip3 install --user ads2bibdesk     # or, from the PyPI index
    pip3 install --user -e .            # or, "Editable" install

To have the MacOS `service <https://support.apple.com/guide/mac-help/use-services-in-apps-mchlp1012/10.14/mac/10.14>`_ (`workflow <https://support.apple.com/guide/automator/create-a-workflow-aut7cac58839/mac>`_) installed at the same time, run one of the following options instead::

    python3 setup.py install --user --service                       # from a local copy
    pip3 install --user --install-option="--service" ads2bibdesk    # from the PyPI index

Usage
~~~~~

Add or update a new article from ADS::

    ads2bibdesk "2013ARA&A..51..105C"
    ads2bibdesk "2019ApJ...873..122D"
    ads2bibdesk "1301.0371"
    ads2bibdesk "2019arXiv190404507R"

**ads2bibdesk** accepts two kinds of article identifier at this moment

- the ADS bibcode of an article (e.g. ``1998ApJ...500..525S``, ``2019arXiv190404507R``)
- the arXiv id of an article (e.g. ``0911.4956``).

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
    
Plan, and a To-Do List
==============================

The current approach is to start the development from a relatively clean-sheet codebase, with the following functions already implemented:

- query the article metadata (title, abstract, BibTeX, etc.) with the new API by article identifiers (no more in-house ADS/arxiv HTML parser functions)
- add/update BibTeX entry using the article identifier
- download article PDFs using the new ADS gateway links and attached them to the BibDesk database
- update the BibDesk database and attached PDFs (by borrowing the BibDesk class from the original ads_bibdesk)
- replace obsolete Python syntax/functions/modules with newer ones, e.g. optparser->argparser, f-string formatting, and use configparser()
- clear up the dependency requirements (let setup.py do the check)
- use an on-campus ``ssh`` proxy machine to download PDFs behind the journal paywall.
- The MacOS Automator workflow is running the shell script rather than a full-on Python program embedded (this is a necessary workaround since Python 3 is not shipped as default yet)

Note: many features from the original ads_bibdesk are gone at this moment: notably, the "ingest" and "preprint-update" modes.
they can be added back in future.



   
