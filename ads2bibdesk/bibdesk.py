"""A module to manage BibDesk publications using AppKit."""

import logging
import os
import subprocess
import textwrap
from typing import Union, Tuple

import AppKit  # installed from pyobjc-framework-Cocoa

app_info = AppKit.NSBundle.mainBundle().infoDictionary()
app_info["LSBackgroundOnly"] = 1

logger = logging.getLogger(__name__)


class BibDesk(object):
    """Manage the BibDesk publications using AppKit."""

    def __init__(self):
        """Initialize the BibDesk object."""
        self.app = AppKit.NSAppleScript.alloc()
        self.refresh()

    def __call__(self, cmd, pid=None, condition=None, include_error=False, to_strlist=False):
        """Run an AppleScript command on the first document of BibDesk

        Args:
            cmd (str): AppleScript command string
            pid (str, optional): Address call to first/last publication of the document. Defaults to None.
            condition (str, optional): Restrict the selection to a subset of publications. Defaults to None.
                Example: '(value of field "Adsurl" contains "arXiv") or (value of field "Adsurl" contains "astro.ph")'
            include_error (bool, optional): Return the full output of the call, including error. Defaults to False.
            to_strlist (bool, optional): Return output as a list of strings, rather than the AppleEventDescriptor object.
                Defaults to False.

        Returns:
            Union[AppleEventDescriptor, Tuple[AppleEventDescriptor, Any]]: Result of the AppleScript command.
                If include_error is True, returns a tuple containing the AppleEventDescriptor and anycode  error encountered.
        """

        # Construct the AppleScript command
        select_cmd = ['tell first document of application "BibDesk" to']

        # Address a subsect of publication if condition is used
        if condition:
            select_cmd.append(f'tell publications whose {condition} to')

        # Address to a single publication instead a group of publications.
        if pid:
            select_cmd.append(f'tell first publication whose id is "{pid}" to')

        select_cmd.append(cmd)
        select_cmd = ' '.join(select_cmd)

        event_desc, event_error = self.app.initWithSource_(select_cmd).executeAndReturnError_(None)
        # event_desc: AppleEventDescriptor object, see more,
        #   https://developer.apple.com/documentation/foundation/nsappleeventdescriptor
        # event_error: Generally this should be None, it could be something else if the BibDesk applescript
        # call is illegal (e.g. ask for name of opened document but no doc is opened).

        # Handle output options
        ret = self.desc_to_strlist(event_desc) if to_strlist else event_desc
        if include_error:
            return ret, event_error
        return ret

    @staticmethod
    def desc_to_strlist(desc: AppKit.NSAppleEventDescriptor) -> list:
        """Convert an AppleEventDescriptor to a list of strings."""
        return [desc.descriptorAtIndex_(i + 1).stringValue() for i in range(desc.numberOfItems())]

    @staticmethod
    def desc_to_str(desc):
        """Convert an AppleEventDescriptor to a string."""
        return desc.stringValue()

    def get_properties(self, property_name: str, condition=None) -> list:
        """Get the list of properties from BibTeX collections.

        Args:
            property_name (str): Name of the property to be returned. 
                E.g., 'title', 'author', 'url', 'value of field "Adsurl"'.
            condition (str, optional): Filter condition. Defaults to None.

        Returns:
            list: List of property values.
        """
        if condition is None:
            return self(f'return {property_name} of publications', to_strlist=True)
        return self(f'return {property_name}', condition=condition, to_strlist=True)

    def refresh(self):
        """Refresh the cached basic BibDesk data."""
        _, event_error = self('return name of first document of application "BibDesk"', include_error=True)
        if event_error is not None:
            self('tell application "BibDesk" to make new document')
        self.titles = self.get_properties('title')
        self.ids = self.get_properties('id')
        self.urls = self.get_properties('url')
        self.adsurls = self.get_properties('value of field "Adsurl"')

    def search_pids_by_title(self, title):
        """Search for publication IDs by title."""
        return [self.ids[idx] for idx, idx_title in enumerate(self.titles) if idx_title == title]

    def get_authors(self, pid):
        """Get the names of authors of a publication as a list"""
        return self('name of authors', pid, to_strlist=True)

    def get_fields(self, pid):
        """Get the fields/values as a dictionary for a single BibDesk entry"""
        return dict((k, v) for k, v in zip(self('return name of fields', pid=pid, to_strlist=True),
                                           self('return value of fields', pid=pid, to_strlist=True)))

    def get_field_names(self, pid):
        """Get the field names of a publication."""
        return self('return name of fields', pid=pid, to_strlist=True)

    def get_note(self, pid):
        """Get the note of a publication."""
        return self('return its note', pid=pid).stringValue()

    def set_note(self, pid, note):
        """Set the note of a publication."""
        self('set its note to "{}"'.format(note), pid)

    def get_citekey(self, pid):
        """Get the citation key of a publication."""
        return self('cite key', pid=pid).stringValue()

    def get_abstract(self, pid):
        """Get the abstract of a publication."""
        return self('abstract', pid=pid).stringValue()

    def get_title(self, pid):
        """Get the abstract of a publication."""
        title = self('title', pid=pid).stringValue()
        if title.startswith('{'):
            title = title[1:]
        if title.endswith('}'):
            title = title[:-1]
        return title

    def get_urls_from_fields(self, pid):
        """Get all URLs from fields of a publication."""
        return self('value of fields whose name ends with "url"', pid=pid, to_strlist=True)

    def get_urls(self, pid):
        """Get URLs linked to a publication."""
        return self('linked URLs', pid=pid, to_strlist=True)

    def set_field_value(self, pid, field, value):
        """Set the value of a field in a publication."""
        self(f'set value of field "{(field, value)}" to "{pid}"')
        return

    def import_from_bibtex(self, bibtex_str):
        """Import a new entry from a BibTeX item."""
        bibtex_str_clean = bibtex_str.replace('\\', r'\\').replace('"', r'\"')
        desc = self(f'import from "{bibtex_str_clean}"')
        pid = desc.descriptorAtIndex_(1).descriptorAtIndex_(3).stringValue()
        self.refresh()
        return pid

    def set_autokey(self, pid):
        """Set the automatic citation key of a publication."""
        self('set cite key to generated cite key', pid=pid)
        return

    def set_abstract(self, pid, abstract):
        """Set the abstract of a publication."""
        abstract_clean = abstract.replace('\\', r'\\').replace('"', r'\"').replace('}', ' ').replace('{', ' ')
        self(f'set abstract to "{abstract_clean}"', pid=pid)
        return

    def get_field(self, pid, field_name):
        """Get the value of a field in a publication."""
        self(f'value of field "{field_name}"', pid=pid).stringValue()
        return

    def set_field(self, pid, field_name, field_value):
        """Set the value of a field in a publication."""
        self(f'set value of field "{(field_name, field_value)}" to "{pid}"')
        return

    def add_file(self, pid, filename, prepend=False):
        """Add a file to the linked files of a publication."""
        if prepend:
            self(f'add POSIX file "{filename}" to beginning of linked files', pid=pid)
        else:
            self(f'add POSIX file "{filename}" to end of linked files', pid=pid)
        return

    def add_url(self, pid, url):
        """Add a URL to a publication."""
        self(f'make new linked URL at end of linked URLs with data "{url}"', pid=pid)
        return

    def autofile(self, pid):
        """Automatically file a publication."""
        self('auto file', pid=pid)
        return

    def safe_delete(self, pid):
        """Safely delete a publication and associated PDFs.
        
        This method will take into account the existence of PDFs with Skim notes.
        """
        keptPDFs = []
        files = self('POSIX path of linked files', pid=pid, to_strlist=True)
        notes = self('text Skim notes of linked files', pid=pid, to_strlist=True)

        for f, n in zip([f for f in files if f is not None],
                        [n for n in notes if n is not None]):
            if f.lower().endswith('pdf'):
                if '_notes_' in f:
                    keptPDFs.append(f)
                else:
                    # check for annotations
                    if n or self.has_annotations(f):
                        suffix = 1
                        path, ext = os.path.splitext(f)
                        backup = path + '_notes_{:d}.pdf'.format(suffix)
                        while os.path.exists(backup):
                            suffix += 1
                            backup = path + '_notes_{:d}.pdf'.format(suffix)
                        # rename
                        os.rename(f, backup)
                        keptPDFs.append(backup)
                        if os.path.exists(path + '.skim'):
                            os.rename(path + '.skim',
                                      path + '_notes_{:d}.skim'.format(suffix))
                    else:
                        # remove file
                        os.remove(f)
        # delete publication
        self('delete', pid=pid)
        self.refresh()
        return keptPDFs

    def get_groups(self, pid):
        """Get the names of the static groups a publication belongs to.

        Args:
            pid (str): BibDesk publication unique id (device-dependent).

        Returns:
            list: A list of group/collection names.
        """

        cmd = """
            tell first document of application "BibDesk"
            set oldPub to ( get first publication whose id is "{}" ) 
            set pGroups to ( get static groups whose publications contains oldPub ) 
            set GroupNames to {{}}
            repeat with aGroup in pGroups 
                copy (name of aGroup) to the end of GroupNames
            end repeat
            return GroupNames 
            end tell
            """.format(pid)
        cmd = textwrap.dedent(cmd)

        output = self.app.initWithSource_(cmd).executeAndReturnError_(None)
        output = output[0]
        output = [output.descriptorAtIndex_(i + 1).stringValue()
                  for i in range(output.numberOfItems())]
        logger.debug("check static groups: pid: {}; static group: {}".format(pid, output))
        return output

    def add_groups(self, pid, groups):
        """Add the publication into static groups.

        Args:
            pid (str): BibDesk publication unique id (device-dependent).
            groups (list): List of group names.
            
        Returns:
            list: A list of group/collection names after adding the publication.

        Note that AppleScript lists are bracked by curly braces with items separate by commas.
        Each item is an alphanumeric label(?) or a string enclosed by double quotes or a list itself
            e.g. { "group1", "groups" }            
        """

        as_groups = ", ".join(['\"'+x+'\"' for x in groups])
        cmd = """
            tell first document of application "BibDesk"
                set newPub to ( get first publication whose id is "{}" )
                #set AppleScript's text item delimiters to return
                repeat with agroup in {{ {} }}
                    set theGroup to get static group agroup
                    add newPub to theGroup
                end repeat
            end tell
            """.format(pid, as_groups)
        cmd = textwrap.dedent(cmd)
        _, _ = self.app.initWithSource_(cmd).executeAndReturnError_(None)
        new_groups = self.get_groups(pid)
        return new_groups

    @staticmethod
    def has_annotations(f):
        """Check if a PDF file has annotations."""

        cmd = "strings {} | grep  -E 'Contents[ ]{{0,1}}\('".format(f)
        check1_annotated_content = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                                    stderr=open('/dev/null', 'w')).stdout.read() != b''

        cmd = "strings {} | grep  -E 'AAPL:AKExtras'".format(f)
        check2_annotated_content = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                                    stderr=open('/dev/null', 'w')).stdout.read() != b''

        # note that b''!=u'' in Python 3
        is_annotated = check1_annotated_content or check2_annotated_content

        return is_annotated
