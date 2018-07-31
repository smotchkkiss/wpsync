from pathlib import Path
from configparser import ConfigParser
from urllib.parse import quote, unquote
import sys
import os
from schema import Schema, Or, Optional, SchemaError


# https://stackoverflow.com/a/377028
def check_required_executable(executable_name):
    paths = os.environ['PATH'].split(os.pathsep)
    for path in paths:
        exec_path = os.path.join(path, executable_name)
        if os.path.isfile(exec_path) and os.access(exec_path, os.X_OK):
            return
    print(f'wpsync requires {executable_name} to be installed on your system.')
    sys.exit(1)


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
                return (validate_config(config._sections), p)
        except FileNotFoundError as e:
            pass

    # if none of them worked out, raise an error
    raise Exception('Config file not found')


def validate_config(config):
    # all options are listed twice, because I don't know how else
    # to express that http_user and http_pass can only be used
    # together
    schema = Schema({str: Or({
        # localhost without http basic auth
        'protocol': 'file',
        Optional('name'): str, # for compatibility, will be ignored
        'base_url': str,
        'base_dir': str,
        Optional('theme'): str,
        'mysql_name': str,
        'mysql_host': str,
        'mysql_user': str,
        'mysql_pass': str,
    }, {
        # localhost with http basic auth
        # (why would that be needed?!)
        'protocol': 'file',
        Optional('name'): str, # for compatibility, will be ignored
        'base_url': str,
        'base_dir': str,
        Optional('theme'): str,
        'mysql_name': str,
        'mysql_host': str,
        'mysql_user': str,
        'mysql_pass': str,
        'http_user': str,
        'http_pass': str,
    }, {
        # FTP hosts without http basic auth
        'protocol': 'ftp',
        Optional('name'): str, # for compatibility, will be ignored
        'base_url': str,
        'base_dir': str,
        'user': str,
        'host': str,
        'pass': str,
        Optional('theme'): str,
        'mysql_name': str,
        'mysql_host': str,
        'mysql_user': str,
        'mysql_pass': str,
    }, {
        # FTP hosts with http basic auth
        'protocol': 'ftp',
        Optional('name'): str, # for compatibility, will be ignored
        'base_url': str,
        'base_dir': str,
        'user': str,
        'host': str,
        'pass': str,
        Optional('theme'): str,
        'mysql_name': str,
        'mysql_host': str,
        'mysql_user': str,
        'mysql_pass': str,
        'http_user': str,
        'http_pass': str,
    }, {
        # SSH hosts without http basic auth
        'protocol': Or('ssh', 'sftp'),
        Optional('name'): str, # for compatibility, will be ignored
        'base_url': str,
        'base_dir': str,
        'user': str,
        'host': str,
        Optional('pass'): str,
        Optional('theme'): str,
        'mysql_name': str,
        'mysql_host': str,
        'mysql_user': str,
        'mysql_pass': str,
    }, {
        # SSH hosts with http basic auth
        'protocol': Or('ssh', 'sftp'),
        Optional('name'): str, # for compatibility, will be ignored
        'base_url': str,
        'base_dir': str,
        'user': str,
        'host': str,
        Optional('pass'): str,
        Optional('theme'): str,
        'mysql_name': str,
        'mysql_host': str,
        'mysql_user': str,
        'mysql_pass': str,
        'http_user': str,
        'http_pass': str,
    })})
    try:
        return schema.validate(config)
    except SchemaError as e:
        print('An error occured while validating the configuration:')
        print(e)
        sys.exit(1)


def get_wpsyncdir(config_path):
    path = config_path.parent
    if path.name != '.wpsync':
        path /= '.wpsync'
    path.mkdir(mode=0o755, exist_ok=True)
    return path


def get_options(arguments):
    return {
        'database': bool(arguments['--database'] or arguments['--all']),
        'uploads': bool(arguments['--uploads'] or arguments['--all']),
        'plugins': bool(arguments['--plugins'] or arguments['--all']),
        'themes': bool(arguments['--themes'] or arguments['--all']),
        'full': arguments['--all'],
    }


def assert_site_exists(config, name):
    if not name in config:
        print(f'Site {name} is not configured.')
        sys.exit(1)


def encode_site_name(plain_site_name):
    return quote(plain_site_name, safe='')


def decode_site_name(encoded_site_name):
    return unquote(encoded_site_name)
