"""wpsync

Synchronise WordPress sites across ssh, (s)ftp and local hosts

Usage:
  wpsync [-v] [-c file] sync ((-d|-u|-p|-t)... | -a | -f) <source> <dest>
  wpsync [-v] [-c file] backup ((-d|-u|-p|-t)... | -a | -f) <source>
  wpsync [-v] [-c file] rollback ((-d|-u|-p|-t)... | -a | -f) [backup] [dest]
  wpsync [-v] [-c file] list ((-d|-u|-p|-t)... | -a | -f) [site]
  wpsync -h | --help
  wpsync -V | --version

Arguments:
  source  Name of a WordPress site from your config file
  dest    Name of a WordPress site from your config file
  site    Name of a WordPress site from your config file
  backup  ID of a specific backup to use

Options:
  -h --help              Output usage information.
  -V --version           Output version number.
  -v --verbose           Print what you're doing.
  -c file --config=file  Use the config file specified.
  -d --database          Sync/Backup/Rollback database.
  -u --uploads           Sync/Backup/Rollback uploads.
  -p --plugins           Sync/Backup/Rollback plugins.
  -t --themes            Sync/Backup/Rollback the theme(s).
  -a --all               Sync/Backup/Rollback all of the above.
  -f --full              Sync/Backup/Rollback the full site.
"""
# The (-d|-u|-p|-t)... thing is a hack to make docopt accept any,
# but at least one of -d, -u, -p, -t.
# https://stackoverflow.com/a/43983602
# A downside is that it will also accept multiple mentions, but I
# think it's still better than spelling out the options like
# (-d [-upt] | -u [-dpt] | -p [-dut] | -t [-dup])
from pathlib import Path
from docopt import docopt
from utils import find_backup_dir, get_config


def sync():
    if arguments['--verbose']:
        print('SYNC')


def backup():
    if arguments['--verbose']:
        print('BACKUP')


def rollback():
    if arguments['--verbose']:
        print('ROLLBACK')


def list_backups():
    if arguments['--verbose']:
        print('LIST')


if __name__ == '__main__':
    arguments = docopt(__doc__, version='PyWpsync 0.0.0')
    config = get_config(arguments['--config'])
    wpsyncdir = find_backup_dir()

    # print(arguments)

    if arguments['sync']:
        sync()
    elif arguments['backup']:
        backup()
    elif arguments['rollback']:
        rollback()
    elif arguments['list']:
        list_backups()
