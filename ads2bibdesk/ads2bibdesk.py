#!/usr/bin/env python

# Standard

import os
import sys

import argparse
from configparser import ConfigParser, ExtendedInterpolation
import difflib
import logging
import tempfile
import subprocess

# Dependent

import ads
import requests

from .bibdesk import BibDesk
from . import __version__

import logging
logger=logging.getLogger(__name__)

def main():
    """
    Parse options and launch main loop
    """
        
    description = """

ads2bibdesk helps you add astrophysics articles listed on NASA/ADS
to your BibDesk database using the ADS Developer API

ads2bibdesk accepts many kinds of article tokens:
 - the ADS bibcode of an article (e.g. 1998ApJ...500..525S, 2019arXiv190404507R), or
 - the arXiv identifier of an article (e.g. 0911.4956).
 - doi of an article (e.g. 10.3847/1538-4357/aafd37)
(Example: `ads2bibdesk "2019arXiv190404507R"`)

Different from J.Sick's original `ads_bibdesk` or `adsbibdesk`, ads2bibdesk require the user
to specify a personal ADS API key (per the new ADS policy). The metadata query will be performed
using the API python client maintained by Andy Casey: 
  http://ads.readthedocs.io

The API key can be written into your ads2bibdesk preference file ~/.ads/ads2bibdesk.cfg, or
saved to ~/.ads/dev_key or saved as an environment variable named ADS_DEV_KEY (following 
the ads python package's instruction)

"""

    
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-d', '--debug',
                        dest="debug", action="store_true",
                        help="Debug mode; prints extra statements")
    
    parser.add_argument('article_identifier',type=str,
                        help="""A required article identifier, which could be:
  - the ADS bibcode of an article, or
  - the arXiv id of an article, or
  - article doi """)

    args = parser.parse_args()
    
    prefs_class=Preferences()
    prefs = prefs_class.prefs
    log_path = prefs_class.log_path
    prefs_path = prefs_class.prefs_path

    if  args.debug==True:
        prefs['options']['debug']='True'
    
    logging.basicConfig(
        level=logging.debug,
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        filename=log_path)  
    if  'true' not in prefs['options']['debug'].lower(): 
        logging.getLogger('').setLevel(logger.info)
    
    ch = logging.StreamHandler()
    ch.setLevel(logger.debug)
    logging.getLogger('').addHandler(ch)

    logger.info("Starting ADS to BibDesk")
    logger.debug("ADS to BibDesk version {}".format(__version__))
    logger.debug("Python: {}".format(sys.version))        
    
    article_status=process_article(args ,prefs)


def process_article(args, prefs):
    """
    """

    bibdesk = BibDesk()
    
    article_status=process_token(args.article_identifier, prefs, bibdesk)
    
    bibdesk.app.dealloc()
    
    return article_status
    
def process_token(article_identifier, prefs, bibdesk):
    """
    Process a single article token from the user, adding it to BibDesk.

    Parameters
    ----------
    article_identifier : str
        Any user-supplied `str` token.
    prefs : :class:`Preferences`
        A `Preferences` instance.
    bibdesk : :class:`BibDesk`
        A `BibDesk` AppKit hook instance.
    """
    
    
    
    """
    print((prefs['default']['ads_token']))
    print(article_identifier)
    """
    
    if  'true' in prefs['options']['alert_sound'].lower():
        alert_sound='Frog'
    else:
        alert_sound=None
    
    if  'dev_key' not in prefs['default']['ads_token']:
        ads.config.token = prefs['default']['ads_token']
    
    ads_query = ads.SearchQuery(identifier=article_identifier,
                              fl=['author','first_author',
                                  'bibcode','identifier','alternate_bibcode','id',
                                  'year', 'title','abstract'])
    try:
        ads_articles = list(ads_query)
    except:
        logger.info("API response error, Likely no authorized key is provided!")
        notify('API response error', 'key:'+prefs['default']['ads_token'], 
               'Likely no authorized key is provided!',alert_sound=alert_sound)
        return False
    
    if  len(ads_articles)!=1:
        logger.debug(
            ' Zero or Multiple ADS entries for the article identifiier: {}'.format(article_identifier))
        logger.debug('Matching Number: {}'.format(len(ads_articles)))
        notify('Found Zero or Multiple ADS antries for ',
                article_identifier, ' No update in BibDesk', alert_sound=alert_sound)
        logger.info("Found Zero or Multiple ADS antries for {}".format(article_identifier))
        logger.info("No update in BibDesk")

        return False
    
    ads_article = ads_articles[0]
    
    use_bibtexabs=False
    #   use "bibtex" by default
    #   another option could be "bibtexabs":
    #       https://github.com/andycasey/ads/pull/109
    #   however, a change in ads() is required and the abstract field from the "bibtexabs" option doesn't
    #   always comply with the tex syntax.     
    if  use_bibtexabs==True:
        ads_bibtex = ads.ExportQuery(bibcodes=ads_article.bibcode,format='bibtexabs').execute()
    else:
        ads_bibtex = ads.ExportQuery(bibcodes=ads_article.bibcode,format='bibtex').execute()

    logger.debug("process_token: >>>API limits")
    logger.debug("process_token:    {}".format(ads_query.response.get_ratelimits()))
    logger.debug("process_token: >>>ads_bibtex")
    logger.debug("process_token:    {}".format(ads_bibtex))

    for k, v in ads_article.items():
        logger.debug('process_token: >>>{}'.format(k))
        logger.debug('process_token:    {}'.format(v))
    
    article_bibcode=ads_article.bibcode
    gateway_url='https://'+prefs['default']['ads_mirror']+'/link_gateway'
    #   https://ui.adsabs.harvard.edu/link_gateway by default
    
    if  'true' in prefs['options']['download_pdf'].lower():
        pdf_filename,pdf_status = process_pdf(article_bibcode,
                                              prefs=prefs,
                                              gateway_url=gateway_url)     
    else:
        pdf_filename='.null'

        
        
    kept_pdfs = []
    kept_fields = {}
    kept_groups=[]    
    
    found = difflib.get_close_matches(ads_article.title[0],bibdesk.titles,n=1,cutoff=.7)
    
    # first author is the same
    if  len(found)>0:
        if  found and difflib.SequenceMatcher(
                None,
                bibdesk.authors(bibdesk.pid(found[0]))[0],
                ads_article.author[0]).ratio() > .6:
            # further comparison on abstract
            abstract = bibdesk('abstract', bibdesk.pid(found[0])).stringValue()
            if not abstract or difflib.SequenceMatcher(
                    None, abstract,
                    ads_article.abstract).ratio() > .6:
                pid = bibdesk.pid(found[0])
                kept_groups=bibdesk.get_groups(pid)
                # keep all fields for later comparison
                # (especially rating + read bool)
                kept_fields = dict((k, v) for k, v in
                                   zip(bibdesk('return name of fields', pid, True),
                                   bibdesk('return value of fields', pid, True))
                                   # Adscomment may be arXiv only
                                   if k != 'Adscomment')
                # plus BibDesk annotation
                kept_fields['BibDeskAnnotation'] = bibdesk(
                    'return its note', pid).stringValue()
                kept_pdfs += bibdesk.safe_delete(pid)
                notify('Duplicate publication removed',
                       article_identifier, ads_article.title[0], alert_sound=alert_sound)
                logger.info('Duplicate publication removed:')
                logger.info(article_identifier)
                logger.info(ads_article.title[0])              
                bibdesk.refresh()

    # add new entry
    ads_bibtex_clean=ads_bibtex.replace('\\', r'\\').replace('"', r'\"')
    pub = bibdesk(f'import from "{ads_bibtex_clean}"')
    
    # pub id
    pub = pub.descriptorAtIndex_(1).descriptorAtIndex_(3).stringValue()
    
    # automatic cite key
    bibdesk('set cite key to generated cite key', pub)

    # abstract
    if ads_article.abstract is not None:
        ads_abstract_clean=ads_article.abstract.replace('\\', r'\\').replace('"', r'\"').replace('}', ' ').replace('{', ' ')
        bibdesk(f'set abstract to "{ads_abstract_clean}"', pub)

    doi = bibdesk('value of field "doi"', pub).stringValue()
    
    if  pdf_filename.endswith('.pdf') and pdf_status:
        # register PDF into BibDesk
        bibdesk(f'add POSIX file "{pdf_filename}" to beginning of linked files', pub)
        # automatic file name
        bibdesk('auto file', pub)
    elif 'http' in pdf_filename and not doi:
        # URL for electronic version - only add it if no DOI link present
        # (they are very probably the same)
        bibdesk(f'make new linked URL at end of linked URLs with data "{pdf_filename}"',pub)

    # add URLs as linked URL if not there yet
    urls = bibdesk('value of fields whose name ends with "url"',
                   pub, strlist=True)
    if  'arxiv' in article_bibcode.lower():
        article_gateway = get_article_gateway(article_bibcode,gateway_url=gateway_url)
        urls+=[article_gateway['eprint_html']]
    
    urlspub = bibdesk('linked URLs', pub, strlist=True)

    for u in [u for u in urls if u not in urlspub]:
        bibdesk(f'make new linked URL at end of linked URLs with data "{u}"', pub)

    # add old annotated files
    for kept_pdf in kept_pdfs:
        bibdesk(f'add POSIX file "{kept_pdf}" to end of linked files', pub)

    # re-insert custom fields
    bibdesk_annotation=kept_fields.pop("BibDeskAnnotation", '')
    bibdesk(f'set its note to "{bibdesk_annotation}"', pub)
    newFields = bibdesk('return name of fields', pub, True)
    for k, v in list(kept_fields.items()):
        if k not in newFields:
            bibdesk(f'set value of field "{(k, v)}" to "{pub}"')
    notify('New publication added',
           bibdesk('cite key', pub).stringValue(),
           ads_article.title[0], alert_sound=alert_sound)
    logger.info('New publication added:')
    logger.info(bibdesk('cite key', pub).stringValue())
    logger.info(ads_article.title[0])

    # add back the static groups assignment
    if  kept_groups!=[]:
        new_groups=bibdesk.add_groups(pub,kept_groups) 
        
    
    return True

    
def process_pdf(article_bibcode,
                prefs=None,
                fulltext_sources=['pub','eprint','ads'],
                gateway_url="https://ui.adsabs.harvard.edu/link_gateway"):
    """
    fulltext_source='PUB' or 'EPRINT'
    the new ads offers PDFs in urls like this:
        https://ui.adsabs.harvard.edu/link_gateway/{bibcode}/{PUB/EPRINT/ADS}_{PDF/HTML}        
    """
    
    article_gateway=get_article_gateway(article_bibcode,gateway_url=gateway_url)

    pdf_status=False
    
    for fulltext_source in fulltext_sources:
        if  'arxiv' in article_bibcode.lower() and 'pub' in fulltext_source.lower():
            continue
        pdf_url = article_gateway[fulltext_source+'_pdf']
        logger.debug("process_pdf_local: {}".format(pdf_url))
        
        response = requests.get(pdf_url,allow_redirects=True,
                            headers={'User-Agent':
                                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 \
                                (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'})
        
        fd, pdf_filename = tempfile.mkstemp(suffix='.pdf')
        if  response.status_code!=404 and response.status_code!=403:
            os.fdopen(fd,'wb').write(response.content)
        
        if  'PDF document' in get_filetype(pdf_filename):
            pdf_status=True
            break        
        
        if  'pub' in fulltext_source and \
            prefs['proxy']['ssh_user']!='None' and prefs['proxy']['ssh_server']!='None':
            logger.debug("process_pdf_proxy: {}".format(pdf_url))
            process_pdf_proxy(pdf_url,pdf_filename,
                              prefs['proxy']['ssh_user'],
                              prefs['proxy']['ssh_server'],
                              port=prefs['proxy']['ssh_port'])
            if  'PDF document' in get_filetype(pdf_filename):
                pdf_status=True
                break
        
    return pdf_filename, pdf_status

def process_pdf_proxy(pdf_url,pdf_filename,user,server,port=22):
    
    cmd1 = 'ssh -p {} {}@{} \"touch /tmp/adsbibdesk.pdf; '.format(port,user,server)
    cmd1 += 'wget -O /tmp/adsbibdesk.pdf '
    cmd1 += '--header=\\"Accept: text/html\\" '
    cmd1 += '--user-agent=\\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 '
    cmd1 += '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36\\" \\"{}\\"\"'.format(pdf_url)
    cmd2 = 'scp -P {} -q {}@{}:/tmp/adsbibdesk.pdf {}'.format(port,user,server,pdf_filename)

    logger.debug("process_pdf_proxy: {}".format(cmd1))
    subprocess.Popen(cmd1, shell=True,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    logger.debug("process_pdf_proxy: {}".format(cmd2))
    subprocess.Popen(cmd2, shell=True,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()    
    
    return

def get_article_gateway(article_bibcode,
                gateway_url="https://ui.adsabs.harvard.edu/link_gateway"):
    """
    fulltext_source='PUB' or 'EPRINT'
    the new ads offers PDFs in urls like this:
        https://ui.adsabs.harvard.edu/link_gateway/2001A%26A...366...62A/{PUB/EPRINT/ADS}_{PDF/HTML}
    note: not necessarily all link works        
    """
        
    ads_gateway={}
    #   from publishers
    ads_gateway['pub_pdf'] = gateway_url+'/'+article_bibcode+'/PUB_PDF'
    ads_gateway['pub_html'] = gateway_url+'/'+article_bibcode+'/PUB_HTML'
    #   from arxiv
    ads_gateway['eprint_pdf'] = gateway_url+'/'+article_bibcode+'/EPRINT_PDF'
    ads_gateway['eprint_html'] = gateway_url+'/'+article_bibcode+'/EPRINT_HTML'
    #   from ads scan
    ads_gateway['ads_pdf'] = gateway_url+'/'+article_bibcode+'/ADS_PDF'
    ads_gateway['ads_html'] = gateway_url+'/'+article_bibcode+'/ADS_SCAN'
        
    return ads_gateway

def get_filetype(filename):
    x = subprocess.Popen('file "{}"'.format(filename), shell=True,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE).stdout.read()
    try:
        return x.decode()
    except:
        return x


    
def notify(title, subtitle, desc, alert_sound='Frog'):
    """
    Publish a notification to Notification Center:
        try the applescript method first, then the "objc" method
     
    note: 
        the applescript method only work with Mavericks (10.9) and later
        alert_sound: 'Frog','Blow', 'Pop' etc. or None
 
    """   
    try:
        if  alert_sound is None:
            subprocess.Popen("""
                      osascript -e 'display notification "{}" with title "{}" subtitle "{}"'
                      """.format(desc,title,subtitle),
                      shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        else:
            subprocess.Popen("""
                      osascript -e 'display notification "{}" with title "{}" subtitle "{}" sound name "{}"'
                      """.format(desc,title,subtitle,alert_sound),
                      shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
 
    except ExplicitException:
        
        try:
            import objc
            notification = objc.lookUpClass('NSUserNotification').alloc().init()
            notification.setTitle_(title)
            notification.setInformativeText_(desc)
            notification.setSubtitle_(subtitle)
            if  alert_sound is not None:
                notification.setSoundName_(alert_sound) # "NSUserNotificationDefaultSoundName"
            objc.lookUpClass('NSUserNotificationCenter').\
                defaultUserNotificationCenter().scheduleNotification_(notification)
            notification.dealloc()  
        except ExplicitException:
            pass


def has_annotationss(f):
    """
    """
    return subprocess.Popen(
        "strings {} | grep  -E 'Contents[ ]{{0,1}}\('".format(f),
        shell=True, stdout=subprocess.PIPE,
        stderr=open('/dev/null', 'w')).stdout.read() != b''     # b''!=u'' in Python 3


class Preferences(object):
    
    def __init__(self):
        """
        """
        
        self.prefs_path = os.path.expanduser('~/.ads/ads2bibdesk.cfg')
        self.log_path = os.path.expanduser('~/.ads/ads2bibdesk.log')
        self.prefs = self._get_prefs()

    
    def _get_prefs(self):
        """
        """
        
        prefs = ConfigParser(interpolation=ExtendedInterpolation())
        prefs.read_string("""
        
            [default]
            ads_mirror = ui.adsabs.harvard.edu
            ads_token = dev_key
            
            [proxy]
            ssh_user = None
            ssh_server = None
            ssh_port = 22
            
            [options]
            download_pdf = True
            alert_sound = True
            debug = False            
                          
            """)
        prefs_dir=os.path.dirname(self.prefs_path)
        
        if  not os.path.exists(prefs_dir):
                os.makedirs(prefs_dir)
        if  not os.path.exists(self.prefs_path):
            with open(self.prefs_path, 'w') as prefs_file:
                prefs.write(prefs_file)
        else:
            prefs.read(self.prefs_path)

        return prefs 

if  __name__ == '__main__':
    
    main()
