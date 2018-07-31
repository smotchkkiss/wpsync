"""wpsync

Synchronise WordPress sites across ssh, (s)ftp and local hosts

Usage:
  wpsync [-v] [-c file] [-l] sync ((-d|-u|-p|-t)... | -a | -f) <source> <dest>
  wpsync [-v] [-c file] [-l] backup ((-d|-u|-p|-t)... | -a | -f) <source>
  wpsync [-v] [-c file] [-l] rollback [(-d|-u|-p|-t)... | -a | -f] [-b backup] [-s site]
  wpsync [-v] [-c file] [-l] list [(-d|-u|-p|-t)... | -a | -f] [-s site]
  wpsync -h | --help
  wpsync -V | --version

Arguments:
  source  Name of a WordPress site from your config file
  dest    Name of a WordPress site from your config file

Options:
  -h --help                  Output usage information.
  -V --version               Output version number.
  -v --verbose               Print what you're doing.
  -c file --config=file      Use the config file specified.
  -l --legacy                Use old name field instead of config section headers.
  -b backup --backup=backup  ID of a specific backup to use.
  -s site --site=site        Specify a site where it's optional.
  -d --database              Sync/Backup/Rollback database.
  -u --uploads               Sync/Backup/Rollback uploads.
  -p --plugins               Sync/Backup/Rollback plugins.
  -t --themes                Sync/Backup/Rollback the theme(s).
  -a --all                   Sync/Backup/Rollback all of the above.
  -f --full                  Sync/Backup/Rollback the full site.
"""
# The (-d|-u|-p|-t)... thing is a hack to make docopt accept any,
# but at least one of -d, -u, -p, -t.
# https://stackoverflow.com/a/43983602
# A downside is that it will also accept multiple mentions, but I
# think it's still better than spelling out the options like
# (-d [-upt] | -u [-dpt] | -p [-dut] | -t [-dup])
from pathlib import Path
from docopt import docopt
from cli_helpers import (
    assert_site_exists,
    check_required_executable,
    encode_site_name,
    get_config,
    get_options,
    get_site,
    get_wpsyncdir,
)
from list_backups import list_backups as _list_backups


def sync():
    assert_site_exists(config, arguments['<source>'], arguments['--legacy'])
    assert_site_exists(config, arguments['<dest>'], arguments['--legacy'])
    if arguments['--verbose']:
        print('SYNC')


def backup():
    assert_site_exists(config, arguments['<source>'], arguments['--legacy'])
    if arguments['--verbose']:
        print('BACKUP')


def rollback():
    if arguments['--site'] is not None:
        assert_site_exists(config, arguments['--site'], arguments['--legacy'])
    if arguments['--verbose']:
        print('ROLLBACK')


def list_backups():
    if arguments['--site'] is not None:
        assert_site_exists(config, arguments['--site'], arguments['--legacy'])
        site_name = arguments['--site']
        if arguments['--legacy']:
            site = [config[_site_name]
                    for _site_name
                    in config.keys()
                    if config[_site_name]['name'] == site_name][0]
            site_names = [(site['name'], site['fs_safe_name'])]
        else:
            site_names = [(site_name, config[site_name]['fs_safe_name'])]
    else:
        if arguments['--legacy']:
            site_names = [(config[site]['name'], config[site]['fs_safe_name'])
                          for site
                          in config.keys()]
        else:
            site_names = [(site, config[site]['fs_safe_name'])
                          for site
                          in config.keys()]
    _list_backups(site_names, wpsyncdir, **options)


if __name__ == '__main__':
    for executable_name in ['cat', 'ssh', 'scp', 'lftp']:
        check_required_executable(executable_name)
    arguments = docopt(__doc__, version='PyWpsync 0.0.0')
    (config, config_path) = get_config(arguments['--config'])
    wpsyncdir = get_wpsyncdir(config_path)
    options = get_options(arguments)

    for site in config:
        if arguments['--legacy']:
            config[site]['fs_safe_name'] = encode_site_name(
                config[site]['name']
            )
        else:
            config[site]['fs_safe_name'] = encode_site_name(site)

    if arguments['sync']:
        sync()
    elif arguments['backup']:
        backup()
    elif arguments['rollback']:
        rollback()
    elif arguments['list']:
        list_backups()
