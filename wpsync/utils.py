from pathlib import Path
from configparser import ConfigParser

config_file_names = [
    'wpsync.config.ini',
    'wpsync.ini',
    '.wpsyncrc',
    '.wpsync/wpsync.config.ini',
    '.wpsync/config.ini',
    '.wpsync/wpsync.ini',
]

def get_config(path):
    config = ConfigParser()

    # make a list of possible config file paths
    if path is not None:
        paths_to_check = [Path(path)]
    else:
        cwd = Path.cwd()
        dirs_to_check = [cwd, *cwd.parents]
        if Path.home() not in dirs_to_check:
            dirs_to_check.append(Path.home())
        paths_to_check = []
        for d in dirs_to_check:
            for f in config_file_names:
                paths_to_check.append(d / f)

    # read the first file that can be opened into the config
    # parser
    for p in paths_to_check:
        try:
            with open(p, 'r') as config_file:
                config.read_string(config_file.read())
                return config
        except FileNotFoundError as e:
            pass

    # if none of them worked out, raise an error
    raise Exception('Config file not found')

def find_backup_dir():
    print('::find_backup_dir::')
