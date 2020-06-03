import os
from configparser import ConfigParser, ExtendedInterpolation

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