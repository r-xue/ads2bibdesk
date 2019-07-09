#!/usr/bin/env python
# encoding: utf-8
"""

The command line script can be installed via one of these commands:

    python3 setup.py install --user     # from a local copy
    pip3 install --user ads2bibdesk     # or, from PyPI
    pip3 install --user -e .            # or, "Editable" install

To have the MacOS service installed at the same time, run one of the following options instead:

    python3 setup.py install --user --service                       # from a local copy
    pip3 install --user --install-option="--service" ads2bibdesk    # from PyPI (broken at this moment)

"""

import os
import re
import logging
import plistlib
import sys

from setuptools import setup, Command
from setuptools.command.install import install

if  sys.version_info < (3, 6):
    raise Exception("ads2bibdesk requires Python 3.6 or higher.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read(fname):
    with open(rel_path(fname), 'r') as fh:
        return fh.read()


def get_version():
    version_file = read('ads2bibdesk.py')
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if  version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

def rel_path(path):
    return os.path.join(os.path.dirname(__file__), path)

class InstallCommand(install):

    description = 'install everything from build directory'
    service_description = 'Build the "Add to BibDesk" service'

    user_options = install.user_options + [
        ('service', None, service_description),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.service = None

    def finalize_options(self):
        print("build service", self.service)
        install.finalize_options(self)

    def run(self):

        install.run(self)

        service = self.service # will be 1 or None
        if  service is not None:

            cl_path=self.install_scripts
            cl_path=cl_path+'/ads2bibdesk'

            service_path = rel_path(os.path.join(
                            "service","Add to BibDesk.workflow",
                            "Contents", "document.wflow"))
            for workflow in [service_path]:
                #print(workflow)
                with open(workflow, 'rb') as fp:
                    pl = plistlib.load(fp)
                    pl['actions'][0]['action']['ActionParameters']['COMMAND_STRING']=cl_path+' "$1"'
                with open(workflow, 'wb') as fp:
                    plistlib.dump(pl, fp)

                logger.info('Saving "{}"'.format(workflow))
            logger.info("Completed ADS to BibDesk build step")

            workflow_ads2bibdesk=rel_path(os.path.join("service","Add to BibDesk.workflow"))
            workflow_ads2bibdesk=workflow_ads2bibdesk.replace(' ','\ ')
            workflow_system='~/Library/Services/'
            logger.info('Copy the workflow from "{}" to "{}"'.format(workflow_ads2bibdesk,workflow_system))
            os.system('cp -rf '+workflow_ads2bibdesk+' '+workflow_system)


setup(
    name='ads2bibdesk',
    version=get_version(),
    author='Rui Xue',
    url="https://github.com/r-xue/ads2bibdesk",
    description="Add articles from the new NASA/SAO ADS to your BibDesk"
                "bibliography (based on ads_bibdesk from J. Sick et al.).",
    long_description=read('README.rst'),
    long_description_content_type="text/x-rst",
    keywords="bibtex astronomy ADS",
    classifiers=['Development Status :: 4 - Beta',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 "Intended Audience :: Science/Research",
                 "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                 "Operating System :: MacOS :: MacOS X",
                 "Topic :: Scientific/Engineering :: Astronomy"],

    py_modules=['ads2bibdesk'],
    include_package_data=True,
    entry_points={'console_scripts': ['ads2bibdesk = ads2bibdesk:main']},
    python_requires='>=3.6, <4',
    install_requires=['ads','requests','pyobjc'],
    project_urls={'Bug Reports': 'https://github.com/r-xue/ads2bibdesk/issues',
                  'Source': 'https://github.com/r-xue/ads2bibdesk/'},
    cmdclass={'install': InstallCommand}
)
