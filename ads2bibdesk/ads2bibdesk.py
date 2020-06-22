#!/usr/bin/env python

# Standard

import os
import sys

import argparse

import difflib
import logging
import tempfile
import subprocess
import socket

# Dependent

import ads
import requests

from .bibdesk import BibDesk
from .prefs import Preferences
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

Different from J.Sick's original `ads_bibdesk` or `adsbibdesk`, ads2bibdesk require the user
to specify a personal ADS API key (per the new ADS policy). The metadata query will be performed
using the API python client maintained by Andy Casey: 
  http://ads.readthedocs.io

The API key can be set with the following options:
 - your ads2bibdesk preference file: ~/.ads/ads2bibdesk.cfg, 
 - the API client key file: ~/.ads/dev_key
 - an environment variable named ADS_DEV_KEY (following the ads python package's instruction)

"""

    
    parser = argparse.ArgumentParser(description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-d', '--debug',
                        dest="debug", action="store_true",
                        help="Debug mode; prints extra statements")
    
    parser.add_argument('article_identifier',type=str,
                        help="""The identifier of an article could be:
  - ADS bibcode (e.g. 1998ApJ...500..525S, 2019arXiv190404507R)
  - arXiv identifier (e.g. 0911.4956).
  - article doi (e.g. 10.3847/1538-4357/aafd37)""")

    args = parser.parse_args()
    
    prefs_class=Preferences()
    prefs = prefs_class.prefs
    log_path = prefs_class.log_path
    prefs_path = prefs_class.prefs_path

    if  args.debug==True:
        prefs['options']['debug']='True'
    
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        filename=log_path)  
    if  'true' not in prefs['options']['debug'].lower(): 
        logging.getLogger('').setLevel(logger.info)
    """
    
    fh = logging.FileHandler(log_path, mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(CustomFormatter())
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(CustomFormatter())

    #toplogger=logging.getLogger('')
    toplogger=logging.getLogger('ads2bibdesk')
    toplogger.setLevel(logging.DEBUG)
    toplogger.handlers=[]
    toplogger.addHandler(fh)
    toplogger.addHandler(ch)
    
    if  'true' not in prefs['options']['debug'].lower():
        ch.setLevel(logging.INFO)
        fh.setLevel(logging.INFO)
        ch.setFormatter('')
    else:
        ch.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)        

    logger.info("Starting ADS to BibDesk")
    logger.debug("ADS to BibDesk version {}".format(__version__))
    logger.debug("Python: {}".format(sys.version))        
    
    article_status=process_article(args ,prefs)


class CustomFormatter(logging.Formatter):
    """
    customized logging formatter which can handle mutiple-line msgs
    """
    def format(self, record:logging.LogRecord):
        save_msg = record.msg
        output = []
        datefmt='%Y-%m-%d %H:%M:%S'
        s = "{} {:<32} {:<8} : ".format(self.formatTime(record, datefmt),
                                          record.name+'.'+record.funcName,
                                          "[" + record.levelname + "]")
        for line in save_msg.splitlines():
            record.msg = line
            output.append(s+line)
            
        output='\n'.join(output)
        record.msg = save_msg
        record.message = output

        return output         

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
    
    #   field-id list:
    #       https://github.com/adsabs/adsabs-dev-api/blob/master/Search_API.ipynb
    #       https://adsabs.github.io/help/search/comprehensive-solr-term-list

    ads_query = ads.SearchQuery(identifier=article_identifier,
                              fl=['author','first_author',
                                  'bibcode','identifier','alternate_bibcode','id',
                                  'year', 'title','abstract','links_data','esources','bibstem'])
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

    logger.debug(">>>API limits")
    logger.debug("   {}".format(ads_query.response.get_ratelimits()))
    logger.debug(">>>ads_bibtex")
    logger.debug("   {}".format(ads_bibtex))

    for k, v in ads_article.items():
        logger.debug('>>>{}'.format(k))
        logger.debug('   {}'.format(v))
    
    article_bibcode=ads_article.bibcode
    article_esources=ads_article.esources

    if  'true' in prefs['options']['download_pdf'].lower():
        pdf_filename,pdf_status = process_pdf(article_bibcode,article_esources,
                                              prefs=prefs)     
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

                notify('Duplicate publication removed',
                       bibdesk('cite key', pid).stringValue(), ads_article.title[0], alert_sound=alert_sound)                       
                logger.info('Duplicate publication removed:')
                logger.info(bibdesk('cite key', pid).stringValue())
                logger.info(ads_article.title[0])   

                kept_pdfs += bibdesk.safe_delete(pid)
                
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
    if  'EPRINT_HTML' in article_esources:
        urls+=[get_esource_link(article_bibcode,esource_type='eprint_html')]
    
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

    
def process_pdf(article_bibcode,article_esources,
                prefs=None,
                esource_types=['pub_pdf','pub_html','eprint_pdf','ads_pdf','author_pdf']):
    """
    article_bibcode:    ADS bibcode
    article_esources:   esources available for this specific article
    esource_types:      the esource type order to try for PDF downloading
                        if one prefer arxiv pdf, set it to:
                            [eprint_pdf','pub_pdf','pub_html',ads_pdf']

    """
    
    pdf_status = False
    pdf_filename = '.null'
    
    # for the joural listed below, we will use the redirected html address to "guess" the PDF link

    html_journals=['Natur','NatAs']
    is_html_journal=any(html_journal in article_bibcode for html_journal in html_journals)

    for esource_type in esource_types:

        # if esource_type is not available, we will not move forward.
        # if pub_pdf is available, we will not use pub_html.

        if  esource_type.upper() not in article_esources:
            continue
        if  'PUB_PDF' in article_esources and esource_type=='pub_html':   
            continue

        esource_url = get_esource_link(article_bibcode,esource_type=esource_type)

        if  esource_type=='pub_html':
            logger.debug("try >>> {}".format(esource_url))
            response = requests.get(esource_url,allow_redirects=True,
                                headers={'User-Agent':
                                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 \
                                    (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'})
            final_esource_url=response.url
            logger.debug("    >>> {}".format(final_esource_url))            
            pdf_url = get_pdf_fromhtml(final_esource_url)
        else:
            pdf_url = esource_url

        logger.debug("try >>> {}".format(pdf_url))
        response = requests.get(pdf_url,allow_redirects=True,
                            headers={'User-Agent':
                                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 \
                                (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'})

        fd, pdf_filename = tempfile.mkstemp(suffix='.pdf')
        if  response.status_code!=404 and response.status_code!=403:
            os.fdopen(fd,'wb').write(response.content)
        
        if  'PDF document' in get_filetype(pdf_filename):
            pdf_status=True
            logger.debug("try succeeded >>> {}".format(pdf_url))
            break
        else:
            logger.debug("try failed >>> {}".format(pdf_url))

        if  'pub' in esource_type and \
            prefs['proxy']['ssh_user']!='None' and prefs['proxy']['ssh_server']!='None':    
            pdf_status=process_pdf_proxy(pdf_url,pdf_filename,
                                        prefs['proxy']['ssh_user'],
                                        prefs['proxy']['ssh_server'],
                                        port=prefs['proxy']['ssh_port'])
            if  pdf_status==True:
                break                                    

    return pdf_filename, pdf_status

def get_pdf_fromhtml(url_html):
    """
    guess the PDF link from the journal article html url, only works for some journals
    """

    url_pdf=url_html+'.pdf'
    
    if  'nature.com' in url_html:
        url_pdf = url_html+'.pdf'
    if  'annualreviews.org' in url_html:
        url_pdf = url_html.replace('/doi/','/doi/pdf/')
    if  'link.springer.com' in url_html:
        url_pdf = url_html.replace('book','content/pdf').replace('article','content/pdf')+'.pdf'

    return url_pdf

def process_pdf_proxy(pdf_url,pdf_filename,user,server,port=22):

    client=socket.gethostname().replace(' ','')
    tmpfile='/tmp/adsbibdesk.{}.pdf'.format(client)
    cmd1 = 'ssh -p {} {}@{} \"touch {}; '.format(port,user,server,tmpfile)
    cmd1 += 'curl --output {} '.format(tmpfile)
    cmd1 += '-J -L --referer \\";auto\\"  '
    cmd1 += '--user-agent \\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 '
    cmd1 += '(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36\\" \\"{}\\"\"'.format(pdf_url)

    cmd2 = 'scp -P {} -q {}@{}:{} {}'.format(port,user,server,tmpfile,pdf_filename)
    
    logger.debug("try >>> {}".format(pdf_url))
    logger.debug("run >>> {}".format(cmd1))
    subprocess.Popen(cmd1, shell=True,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    logger.debug("run >>> {}".format(cmd2))
    subprocess.Popen(cmd2, shell=True,
             stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()    
    
    if  'PDF document' in get_filetype(pdf_filename):
        pdf_status=True
        logger.debug("try succeeded >>> {}".format(pdf_url))
    else:
        pdf_status=False
        logger.debug("try failed >>> {}".format(pdf_url))

    return pdf_status

def get_esource_link(article_bibcode,esource_type='pub_pdf',
                gateway_url="https://ui.adsabs.harvard.edu/link_gateway"):
    """
    ADS offers esource urls like this:
        https://ui.adsabs.harvard.edu/link_gateway/2001A%26A...366...62A/{PUB/EPRINT/ADS}_{PDF/HTML}
    
    Possible esource_type:
        from publishers:    PUB_PDF, PUB_HTML
        from arxiv:         EPRINT_PDF, EPRINT_HTML
        from ADS:           ADS_PDF, ADS_SCAN
        from author:        AUTHOR_PDF

    note: not necessarily all esources are available for a article (please check fl='links_data')

    """
    return gateway_url+'/'+article_bibcode+'/'+esource_type.upper()

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

        from Foundation import NSUserNotification
        from Foundation import NSUserNotificationCenter

        notification = NSUserNotification.alloc().init()
        center = NSUserNotificationCenter.defaultUserNotificationCenter()

        notification.setTitle_(title)
        notification.setInformativeText_(desc)
        notification.setSubtitle_(subtitle)
        if  alert_sound is not None:
            notification.setSoundName_(alert_sound) # "NSUserNotificationDefaultSoundName"
        #notification.setIdentifier_('org.python.python3')
        center.deliverNotification_(notification)
        notification.dealloc() 
    
    except ExplicitException:
        
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
            pass

if  __name__ == '__main__':
    
    main()
