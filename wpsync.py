"""wpsync
Synchronise WordPress sites across ssh and (s)ftp hosts

Usage:
  wpsync [-v] [-c file] sync [[-dupt] | [-a] | [-f]] <source> <dest>
  wpsync [-v] [-c file] backup [[-dupt] | [-a] | [-f]] <source>
  wpsync [-v] [-c file] rollback [[-dupt] | [-a] | [-f]] [backup] [dest]
  wpsync [-v] [-c file] list [[-dupt] | [-a] | [-f]] [site]
  wpsync -h | --help
  wpsync -V | --version

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
from docopt import docopt


if __name__ == '__main__':
    arguments = docopt(__doc__, version='PyWpsync 0.0.0')
    print(arguments)
