import os
import json
from shlex import quote


# a class to check which executables exists on a host
class HostInfo:
    def __init__(self, wpsyncdir, site, connection):
        self.wpsyncdir = wpsyncdir
        self.site = site
        self.connection = connection
        try:
            info_file = os.path.join(wpsyncdir, 'info',
                                     site['fs_safe_name'] + '.json')
            with open(info_file, 'r') as f:
                self.info = json.load(f)
        except FileNotFoundError:
            self.info = {}

    def __getattr__(self, name):
        if name not in self.info:
            res = self.connection.shell(f'which {quote(name)}')
            self.info[name] = name in res
            info_file = os.path.join(self.wpsyncdir, 'info',
                                     self.site['fs_safe_name'] + '.json')
            with open(info_file, 'w') as f:
                json.dump(self.info, f)
        return self.info[name]
