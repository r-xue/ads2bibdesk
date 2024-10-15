#!/usr/bin/env python

import argparse
import datetime
import difflib
import logging
import os
import re
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
from collections import Counter

import ads
import requests
from lxml import html

from . import __version__
from .bibdesk import BibDesk
from .prefs import Preferences

logger = logging.getLogger(__name__)


def main():
    """Parse options and launch main loop."""
    description = r"""

        ads2bibdesk helps you add astrophysics articles listed on NASA/ADS to your BibDesk database
        using the ADS Developer API

        Different from J.Sick's original `ads_bibdesk` or `adsbibdesk`, ads2bibdesk require the user
        to specify a personal ADS API key (per the new ADS policy). The metadata query will be performed
        using the API python client maintained by Andy Casey: 
        http://ads.readthedocs.io

        The API key can be set with the following options:
            * your ads2bibdesk preference file: ~/.ads/ads2bibdesk.cfg, 
            * the API client key file: ~/.ads/dev_key
            * an environment variable named ADS_DEV_KEY (following the ads python package's instruction)

        """

    parser = argparse.ArgumentParser(description=textwrap.dedent(description),
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-d', '--debug',
                        dest="debug", action="store_true",
                        help="Debug mode with verbose logging messages")

    parser.add_argument('-m', '--merge-duplicate',
                        dest="update_duplicate", action="store_true",
                        help="Merge/update entries with duplicated local ADS bibcode")

    article_identifier_help = """\
        The identifier of an article could be:
            * ADS bibcode (e.g. 1998ApJ...500..525S, 2019arXiv190404507R)
            * arXiv identifier (e.g. 0911.4956).
            * article doi (e.g. 10.3847/1538-4357/aafd37)
        """

    help_text = """
        Check arXiv entries for the newer bibcodes/metadata/PDFs and update if necessary. 
        Optionally it accepts a string specifying the published date range in the format 
        of 'MM/YY-MM/YY'; Examples:
            01/24-          check arXiv entries published from Jan 2024 up to today
            -01/24          check entries published before Jan 2024.
            01/24-05/24     check entries published from Jan 2024 to May 2024
        If no value is specified, all arXiv entries will be examined.
        """
    parser.add_argument(
        '-u', '--update-arxiv', type=str, nargs='?', metavar='mm/yy-mm/yy', 
        dest='update_arxiv', default=None, const='-',
        help=textwrap.dedent(help_text))

    parser.add_argument('article_identifier', type=str, nargs='?',
                        help=textwrap.dedent(article_identifier_help))

    args = parser.parse_args()

    prefs_class = Preferences()
    prefs = prefs_class.prefs
    log_path = prefs_class.log_path

    if args.debug:
        prefs['options']['debug'] = 'True'

    fh = logging.FileHandler(log_path, mode='a')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(CustomFormatter())

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(CustomFormatter())

    a2b_logger = logging.getLogger('ads2bibdesk')
    a2b_logger.setLevel(logging.DEBUG)
    a2b_logger.handlers = []
    a2b_logger.addHandler(fh)
    a2b_logger.addHandler(ch)

    if 'true' in prefs['options']['debug'].lower():
        ch.setLevel(logging.DEBUG)
        fh.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
        fh.setLevel(logging.INFO)
        ch.setFormatter('')

    logger.info("")
    logger.info("Starting ADS to BibDesk")
    logger.debug("ADS to BibDesk version {}".format(__version__))
    logger.debug("Python: {}".format(sys.version))

    if args.update_arxiv:
        _ = update_arxiv(args.update_arxiv, prefs)
    if args.update_duplicate:
        _ = update_duplicate(prefs)
    if args.article_identifier is not None:
        _ = process_article(args.article_identifier, prefs)


class CustomFormatter(logging.Formatter):
    """Customized logging formatter which can handle multiple-line messages."""

    def format(self, record: logging.LogRecord):
        save_msg = record.msg
        output = []
        datefmt = '%Y-%m-%d %H:%M:%S'
        s = "{} {:<32} {:<8} : ".format(self.formatTime(record, datefmt),
                                        record.name+'.'+record.funcName,
                                        "[" + record.levelname + "]")
        for line in save_msg.splitlines():
            record.msg = line
            output.append(s+line)

        output = '\n'.join(output)
        record.msg = save_msg
        record.message = output

        return output


def update_duplicate(prefs):
    """Remove duplicated ADS bibtext items from the BibDesk database.

    This function identifies entries with duplicated ADS bibcodes in the BibDesk database
    and removes them to ensure data consistency.

    Parameters:
        prefs (dict): Preferences for article processing, including proxy settings.

    """
    # Get the ADS canonical bibcode when entries are imported last time and search for duplicated ADS bibcode.
    # note that '' means no adsurl field or its value is empty for that publication entry is empty
    bibdesk = BibDesk()
    adsurl_list = bibdesk.get_properties('value of field "Adsurl"')
    ads_bibcodes = [u.split('bib_query?')[-1].split('abs/')[-1] for u in adsurl_list]
    counts = Counter(ads_bibcodes)
    bibcodes_duplicated = {element: count for element, count in counts.items() if (count > 1 and element)}
    bibdesk.app.dealloc()

    if not bibcodes_duplicated:
        logger.info('Found no entries with duplicated ADS bibcodes. Nothing to update...')
        sys.exit()

    logger.info(f'Updating {len(bibcodes_duplicated)} publication(s) with duplicated local ADS bibcode entries from ADS...')
    process_article_batch(bibcodes_duplicated, prefs, skip_bibcode=False)


def update_arxiv(daterange, prefs):
    """Check and update entries with arXiv-style local ADS bibcodes in the Adsurl field.

    Parameters:
        daterange (str): A string specifying the month/year range in the format [MM/YY]-[MM/YY].
        prefs (dict): Preferences for article processing, including proxy settings.

    Raises:
        AssertionError: If the daterange format is incorrect.

    """
    # Splitting the daterange into from_date and to_date
    daterange_list = daterange.split('-')
    assert len(daterange_list) == 2, "The month/year range needs to be specified in a [MM/YY]-[MM/YY] format."

    from_date = daterange_list[0]
    to_date = daterange_list[1]
    assert from_date == '' or re.match('^\d{2}/\d{2}$', from_date) is not None, \
        'the start month/year needs to be specified in a MM/YY format'
    assert to_date == '' or re.match('^\d{2}/\d{2}$', to_date) is not None, \
        'the end month/year range needs to be specified in a MM/YY format'

    def b2d(bibtex):
        """BibTex -> publication date"""
        m = re.search('month = \{?(\w*)\}?', bibtex).group(1)
        y = re.search('year = \{?(\d{4})\}?', bibtex).group(1)
        return datetime.datetime.strptime(m + y, '%b%Y')

    def recent(added, fdate, tdate):
        fromdate = fdate != '' and datetime.datetime.strptime(fdate, '%m/%y') or datetime.datetime(1900, 1, 1)
        todate = tdate != '' and datetime.datetime.strptime(tdate, '%m/%y') or datetime.datetime(3000, 1, 1)
        logger.debug(f'update arXiv from {fromdate} to {todate}')
        return fromdate <= added <= todate

    bibdesk = BibDesk()
    arxiv_ids = []

    # check for Adsurl containing arxiv or astro.ph bibcodes
    condition = '(value of field "Adsurl" contains "arXiv") or (value of field "Adsurl" contains "astro.ph")'
    adsurl_list = bibdesk.get_properties('value of field "Adsurl"', condition=condition)
    bibtex_list = bibdesk.get_properties('bibtex string', condition=condition)

    # select the ones from the specified mm/yy range
    arxiv_ids = [u.split('bib_query?')[-1].split('abs/')[-1] for u in adsurl_list]
    dates = [b2d(b) for b in bibtex_list]
    arxiv_ids = [b for d, b, c in zip(dates, arxiv_ids, bibtex_list) if recent(d, from_date, to_date)]

    bibdesk.app.dealloc()

    if not arxiv_ids:
        logger.info('Found no entries with arxiv-style ADS bibcode. Nothing to update!')
        sys.exit()

    logger.info(f'Checking {len(arxiv_ids)} publication(s) with arXiv-style local ADS bibcode entries for changes...')

    process_article_batch(arxiv_ids, prefs, skip_bibcode=True)


def process_article_batch(identifiers, prefs, skip_bibcode=False, interval=1):
    """Process a batch of article identifiers.

    Parameters:
        identifiers (list): List of article identifiers to be processed.
        prefs (dict): Preferences for article processing, including proxy settings.
        skip_bibcode (bool, optional): Flag indicating whether to skip processing the bibcode. Defaults to False.
        interval (int, optional): Time interval (in seconds) to wait between processing each article. Defaults to 1.
    """
    # Get the total number of identifiers
    ncheck = len(identifiers)

    # Iterate through each identifier in the batch
    for idx, identifier in enumerate(identifiers):
        # Sleep for the specified interval to prevent flooding the ADS server
        time.sleep(interval)

        # Log the processing progress
        logger.info(f"Processing {idx+1}/{ncheck}: using the article identifier - {identifier}")
        logger.debug('-'*100)

        # Process the current article identifier
        process_article(identifier, prefs, skip_bibcode=skip_bibcode)


def process_article(article_identifier, prefs, skip_bibcode=False):
    """Process an article request.

    Parameters:
        article_identifier (str): The identifier of the article to be processed.
        prefs (dict): Preferences for article processing, including proxy settings.
        skip_bibcode (bool, optional): Flag indicating whether to skip processing the bibcode. Defaults to False.

    Returns:
        bool: The status of the article processing.
    """
    # Initialize BibDesk
    bibdesk = BibDesk()

    # Process the article token
    article_status = process_token(article_identifier, prefs, bibdesk, skip_bibcode=skip_bibcode)

    # Deallocate BibDesk
    bibdesk.app.dealloc()

    return article_status


def process_token(article_identifier, prefs, bibdesk, skip_bibcode=False):
    """Process a single article token from the user, adding it to BibDesk.

    Parameters
    ----------
    article_identifier : str
        Any user-supplied `str` token.
    prefs : :class:`Preferences`
        A `Preferences` instance.
    bibdesk : :class:`BibDesk`
        A `BibDesk` AppKit hook instance.
    skip_bibcode: if identifider is the same as the online ADS bibcode (id), then skip processing
        this is mostly used for update the recent ArViX entries not matured into the final Journal-based BibCode

    """

    if 'true' in prefs['options']['alert_sound'].lower():
        alert_sound = 'Frog'
    else:
        alert_sound = None

    if 'dev_key' not in prefs['default']['ads_token']:
        ads.config.token = prefs['default']['ads_token']

    #   field-id list:
    #       https://github.com/adsabs/adsabs-dev-api/blob/master/Search_API.ipynb
    #       https://adsabs.github.io/help/search/comprehensive-solr-term-list

    ads_query = ads.SearchQuery(identifier=article_identifier,
                                fl=['author', 'first_author',
                                    'bibcode', 'identifier', 'alternate_bibcode', 'id',
                                    'year', 'title', 'abstract', 'links_data', 'esources', 'bibstem'])
    try:
        ads_articles = list(ads_query)
    except:
        logger.info("API response error, Likely no authorized key is provided!")
        notify('API response error', 'key:'+prefs['default']['ads_token'],
               'Likely no authorized key is provided!', alert_sound=alert_sound)
        return False

    logger.debug("API limits {}".format(ads_query.response.get_ratelimits()))

    if not ads_articles:
        notify('Found Zero ADS entry for', article_identifier, 'No update in BibDesk', alert_sound=alert_sound)
        logger.warning("Found Zero ADS entry for the article identifier: {}".format(article_identifier))
        logger.warning("No update in BibDesk")
        return False

    if len(ads_articles) > 1:
        notify('Found Multiple ADS entries for',
               article_identifier, 'Update with the first entry in BibDesk', alert_sound=alert_sound)
        logger.warning("Found Multiple ADS entries for the article identifier: {}".format(article_identifier))
        logger.warning('Matching Number: {}'.format(len(ads_articles)))
        logger.warning('Update with the first entry in BibDesk')

    ads_article = ads_articles[0]
    logger.info(f'Query identifier  : {article_identifier}')
    logger.info(f'ADS return        : {ads_article.bibcode} | {ads_article.alternate_bibcode}')

    if skip_bibcode:
        if article_identifier == ads_article.bibcode:
            logger.info('The latest ADS bibcode is identical to the query article identifier, skip processing.')
            return False
        else:
            logger.info(f'Updating from {article_identifier} to {ads_article.bibcode}')

    for k, v in ads_article.items():
        logger.debug('article/{}: {}'.format(k, v))

    bibcode_checklist = [ads_article.bibcode]
    if ads_article.alternate_bibcode is not None:
        bibcode_checklist.extend(ads_article.alternate_bibcode)
    bibcode_checklist = list(dict.fromkeys(bibcode_checklist))

    use_bibtexabs = False
    #   use "bibtex" by default
    #   another option could be "bibtexabs":
    #       https://github.com/andycasey/ads/pull/109
    #   however, a change in ads() is required and the abstract field from the "bibtexabs" option doesn't
    #   always comply with the tex syntax.
    if use_bibtexabs:
        ads_bibtex = ads.ExportQuery(bibcodes=ads_article.bibcode, format='bibtexabs').execute()
    else:
        ads_bibtex = ads.ExportQuery(bibcodes=ads_article.bibcode, format='bibtex').execute()

    logger.debug("ADS_BIBTEX:")
    logger.debug("{}".format(ads_bibtex))

    article_bibcode = ads_article.bibcode
    article_esources = ads_article.esources

    if 'true' in prefs['options']['download_pdf'].lower():
        pdf_filename, pdf_status = process_pdf(article_bibcode, article_esources, prefs=prefs)
    else:
        pdf_filename = '.null'

    # Initial variables for aggregating information
    kept_pdfs = []
    kept_fields = {'BibDeskAnnotation': ''}
    kept_groups = []
    pids_delete = []

    # add all BibDesk entries with a local ADS bibcode matching the online ADS bibcode or alternate_bibcode into the to-be-removed pid list.
    ads_bibcodes = [u.split('bib_query?')[-1].split('abs/')[-1] for u in bibdesk.adsurls]
    pids_delete.extend(bibdesk.ids[idx] for idx, bibcode in enumerate(ads_bibcodes) if (bibcode in bibcode_checklist and bibcode))

    # add all BibDesk entries simimilar enough the the ADS query results.
    # match similar titles in BibDesk
    for similar_title in difflib.get_close_matches(ads_article.title[0], bibdesk.titles, n=3, cutoff=.7):
        for pid in bibdesk.search_pids_by_title(similar_title):
            # match similar author list
            authors_bibdesk = ' '.join(bibdesk.get_authors(pid)).replace('{', '').replace('}', '')
            authors_ads = ' '.join(ads_article.author)
            if difflib.SequenceMatcher(None, authors_bibdesk, authors_ads).ratio() < .8:
                continue
            # further compare the abstract string
            abstract = bibdesk.get_abstract(pid)
            if not abstract or difflib.SequenceMatcher(None, abstract, ads_article.abstract).ratio() > .6:
                pids_delete.append(pid)

    # remove duplicated pids in the to-be-removed list
    pids_delete = list(dict.fromkeys(pids_delete))

    for pid in pids_delete:

        kept_groups.extend(bibdesk.get_groups(pid))
        # keep all fields for later comparison (especially rating + read bool)
        kept_fields.update(bibdesk.get_fields(pid))
        # Adscomment may be arXiv only
        kept_fields.pop('Adscomment', None)
        # plus BibDesk annotation

        kept_fields['BibDeskAnnotation'] += bibdesk.get_note(pid)

        duplicate_citekey = bibdesk.get_citekey(pid)
        duplicate_title = bibdesk.get_title(pid)
        print(duplicate_citekey)
        notify('Duplicate publication removed',
               duplicate_citekey, ads_article.title[0], alert_sound=alert_sound)
        logger.info('Duplicate publication removed:')
        logger.info(' citekey: '+duplicate_citekey)
        logger.info(' title:   '+duplicate_title)

        kept_pdfs += bibdesk.safe_delete(pid)

    # add new entry
    pub = bibdesk.import_from_bibtex(ads_bibtex)

    # automatic cite key
    bibdesk.set_autokey(pub)

    # abstract
    if ads_article.abstract is not None:
        bibdesk.set_abstract(pub, ads_article.abstract)

    doi = bibdesk.get_field(pub, 'doi')

    if pdf_filename.endswith('.pdf') and pdf_status:
        # register PDF into BibDesk
        bibdesk.add_file(pub, pdf_filename)
        # automatic file name
        bibdesk.autofile(pub)
    elif 'http' in pdf_filename and not doi:
        # URL for electronic version - only add it if no DOI link present
        # (they are very probably the same)
        bibdesk.add_url(pub, pdf_filename)

    # add URLs as linked URL if not there yet
    urls_from_friends = bibdesk.get_urls_from_fields(pub)
    if 'EPRINT_HTML' in article_esources:
        urls_from_friends += [get_esource_link(article_bibcode, esource_type='eprint_html')]

    urls_linked = bibdesk.get_urls(pub)

    for u in [u for u in urls_from_friends if u not in urls_linked]:
        bibdesk.add_url(pub, u)

    # add old annotated files
    for kept_pdf in kept_pdfs:
        bibdesk.add_file(pub, kept_pdf)

    # re-insert custom fields
    bibdesk_annotation = kept_fields.pop("BibDeskAnnotation", '')
    bibdesk.set_note(pub, bibdesk_annotation)
    newFields = bibdesk.get_field_names(pub)
    for k, v in list(kept_fields.items()):
        if k not in newFields:
            bibdesk.set_field_value(pub, k, v)

    new_citekey = bibdesk.get_citekey(pub)
    notify('New publication added', new_citekey, ads_article.title[0], alert_sound=alert_sound)
    logger.info('New publication added:')
    logger.info(' citekey: '+new_citekey)
    logger.info(' title:   '+ads_article.title[0])

    # add back the static groups assignment
    if not kept_groups:
        _ = bibdesk.add_groups(pub, kept_groups)

    return True


def process_pdf(article_bibcode, article_esources, prefs=None, 
                esource_types=['pub_pdf', 'pub_html', 'eprint_pdf', 'ads_pdf', 'author_pdf']):
    """Process PDF file related operations.

    Parameters:
        article_bibcode (str): The ADS bibcode of the article.
        article_esources (list): List of esources available for this specific article.
        prefs (dict): Preferences for PDF processing, including proxy settings.
        esource_types (list): The order of esource types to try for PDF downloading.

    Returns:
        tuple: A tuple containing the path to the downloaded PDF file and a boolean indicating the download status.
    """
    pdf_status = False
    pdf_filename = '.null'

    for esource_type in esource_types:
        # Skip if esource_type is not available or if pub_pdf is available (since it may not point to the actual PDF)
        if esource_type.upper() not in article_esources or esource_type == 'pub_pdf':
            continue

        esource_url = get_esource_link(article_bibcode, esource_type=esource_type)

        # Determine the PDF URL based on esource type
        if esource_type == 'pub_html':
            logger.debug("Try: {}".format(esource_url))
            response = requests.get(esource_url, allow_redirects=True, headers={
                                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'})
            logger.debug("    >>> {}".format(response.url))
            pdf_url = get_pdf_fromhtml(response)
        else:
            pdf_url = esource_url

        logger.debug("Try: {}".format(pdf_url))
        response = requests.get(pdf_url, allow_redirects=True, headers={
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'})

        fd, pdf_filename = tempfile.mkstemp(suffix='.pdf')
        if response.status_code not in [404, 403]:
            os.fdopen(fd, 'wb').write(response.content)

        # Check if downloaded file is a PDF
        if 'PDF document' in get_filetype(pdf_filename):
            pdf_status = True
            logger.debug("Try succeeded >>> {}".format(pdf_url))
            break
        else:
            logger.debug("Try failed >>> {}".format(pdf_url))

        # If preference settings for proxy are available, attempt proxy download
        if 'pub' in esource_type and prefs and prefs['proxy']['ssh_user'] != 'None' and prefs['proxy']['ssh_server'] != 'None':
            pdf_status = process_pdf_proxy(pdf_url, pdf_filename,
                                           prefs['proxy']['ssh_user'],
                                           prefs['proxy']['ssh_server'],
                                           port=prefs['proxy']['ssh_port'])
            if pdf_status:
                break

    return pdf_filename, pdf_status


def get_pdf_fromhtml(response):
    """
    Guesses the PDF link from the journal article HTML URL.

    Only works for some journals.

    Parameters:
        response (requests.Response): The response object containing the HTML of the journal article.

    Returns:
        str: The URL of the PDF version of the article, if found; otherwise, the original HTML URL.
    """
    # Extracting the URL of the HTML page
    url_html = response.url

    # Initializing the PDF URL with the HTML URL
    url_pdf = url_html + '.pdf'

    # Parsing the HTML content
    tree = html.fromstring(response.content)

    # Checking if a specific meta tag exists for the PDF URL
    citation_pdf_url = tree.xpath("//meta[@name='citation_pdf_url']/@content")
    if citation_pdf_url:
        url_pdf = citation_pdf_url[0]

    # Handling specific cases for different journal websites
    if 'annualreviews.org' in url_html:
        url_pdf = url_html.replace('/doi/', '/doi/pdf/')

    if 'link.springer.com' in url_html:
        url_pdf = url_html.replace('book', 'content/pdf').replace('article', 'content/pdf') + '.pdf'

    return url_pdf


def process_pdf_proxy(pdf_url, pdf_filename, user, server, port=22):
    """Download a PDF file through a proxy server using SSH and SCP.

    Parameters:
        pdf_url (str): The URL of the PDF file to download.
        pdf_filename (str): The name of the local file to save the downloaded PDF.
        user (str): The username for SSH authentication on the proxy server.
        server (str): The address of the proxy server.
        port (int, optional): The port number for SSH on the proxy server. Defaults to 22.

    Returns:
        bool: True if the PDF file was successfully downloaded and saved, False otherwise.

    """
    client = socket.gethostname().replace(' ', '')
    tmpfile = f'/tmp/adsbibdesk.{client}.pdf'

    # Constructing the SSH command to download the PDF
    ssh_command = (
        f'ssh -p {port} {user}@{server} "touch {tmpfile}; '
        f'curl --output {tmpfile} -J -L --referer \\";auto\\" '
        f'--user-agent \\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 '
        f'(KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36\\" \\"{pdf_url}\\""'
    )

    # Constructing the SCP command to copy the downloaded PDF to local filesystem
    scp_command = f'scp -P {port} -q {user}@{server}:{tmpfile} {pdf_filename}'

    logger.debug(f"Downloading PDF: {pdf_url}")
    logger.debug(f"Running SSH command: {ssh_command}")
    subprocess.Popen(ssh_command, shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    logger.debug(f"Running SCP command: {scp_command}")
    subprocess.Popen(scp_command, shell=True,
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    # Checking if the downloaded file is a PDF
    if 'PDF document' in get_filetype(pdf_filename):
        pdf_status = True
        logger.debug(f"Download succeeded: {pdf_url}")
    else:
        pdf_status = False
        logger.debug(f"Download failed: {pdf_url}")

    return pdf_status


def get_esource_link(article_bibcode, esource_type='pub_pdf',
                     gateway_url="https://ui.adsabs.harvard.edu/link_gateway"):
    """Construct the URL for accessing a specific type of electronic resource associated with an article.

    Parameters:
        article_bibcode (str): The bibcode of the article.
        esource_type (str, optional): The type of electronic resource. Defaults to 'pub_pdf'.
        gateway_url (str, optional): The base URL for the ADS gateway. Defaults to "https://ui.adsabs.harvard.edu/link_gateway".

    Returns:
        str: The URL for accessing the specified electronic resource.

    Notes:
        ADS offers electronic source (esource) URLs in the following format:
        {gateway_url}/{article_bibcode}/{esource_type}

        Possible esource_type values:
        - From publishers: 'PUB_PDF', 'PUB_HTML'
        - From arXiv: 'EPRINT_PDF', 'EPRINT_HTML'
        - From ADS: 'ADS_PDF', 'ADS_SCAN'
        - From author: 'AUTHOR_PDF'

        Note that not all esources may be available for a given article. It's recommended to check the 'links_data' field.

    """
    return f"{gateway_url}/{article_bibcode}/{esource_type.upper()}"


def get_filetype(filename):
    """
    Get the type of a file using the 'file' command.

    Parameters:
        filename (str): The path to the file.

    Returns:
        str: The file type as determined by the 'file' command.

    """
    try:
        # Run the 'file' command to determine the file type
        result = subprocess.run(['file', filename], capture_output=True, text=True)
        # Extract the file type from the command output
        file_type = result.stdout.strip()
        return file_type
    except Exception as e:
        # If an error occurs, return an empty string
        return ''


def notify(title, subtitle, desc, alert_sound='Frog'):
    """Publish a notification to Notification Center using applescript.

    Args:
        title (str): The title of the notification.
        subtitle (str): The subtitle of the notification.
        desc (str): The description or main message of the notification.
        alert_sound (str): Optional. The sound to play with the notification.
            Options include: 'Frog', 'Blow', 'Pop', etc. Pass None for no sound.

    Note:
        The applescript method only works with macOS 10.9 (Mavericks) and later.
    """
    try:
        from Foundation import NSUserNotification, NSUserNotificationCenter

        notification = NSUserNotification.alloc().init()
        center = NSUserNotificationCenter.defaultUserNotificationCenter()

        notification.setTitle_(title)
        notification.setInformativeText_(desc)
        notification.setSubtitle_(subtitle)
        if alert_sound is not None:
            notification.setSoundName_(alert_sound)

        center.deliverNotification_(notification)
        notification.dealloc()

    except Exception:
        # Fall back to using subprocess and osascript for older versions of macOS
        try:
            osascript_command = 'display notification "{}" with title "{}" subtitle "{}"'
            if alert_sound is not None:
                osascript_command += ' sound name "{}"'
            osascript_command = osascript_command.format(desc, title, subtitle, alert_sound)

            subprocess.Popen(['osascript', '-e', osascript_command],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

        except Exception:
            pass


if __name__ == '__main__':
    main()
