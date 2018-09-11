"""wpsync

Synchronise WordPress sites across ssh, (s)ftp and local hosts

Usage:
  wpsync [-v] [-c file] [-l] sync ((-d|-u|-p|-t)... | -a | -f) <source> <dest>
  wpsync [-v] [-c file] [-l] backup ((-d|-u|-p|-t)... | -a | -f) <source>
  wpsync [-v] [-c file] [-l] rollback [(-d|-u|-p|-t)... | -a | -f] [-b backup] [-s site]
  wpsync [-v] [-c file] [-l] list [(-d|-u|-p|-t)... | -a | -f] [-s site]
  wpsync [-v] [-c file] [-l] install <site>
  wpsync -h | --help
  wpsync -V | --version

Arguments:
  source  Name of a WordPress site from your config file
  dest    Name of a WordPress site from your config file
  site    Name of a WordPress site from your config file

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
import sys
import re
from docopt import docopt
from cli_helpers import (
    assert_site_exists,
    check_required_executable,
    encode_site_name,
    get_config,
    get_options,
    get_wpsyncdir,
)
from connection import connect
from backup import backup as _backup
from rollback import rollback as _rollback
from list_backups import list_backups as _list_backups
from install import install as _install


def sync():
    assert_site_exists(config, arguments['<source>'])
    assert_site_exists(config, arguments['<dest>'])
    source = config[arguments['<source>']]
    dest = config[arguments['<dest>']]
    with connect(source) as connection:
        backup_id = _backup(wpsyncdir, source, connection,
                            arguments['--verbose'], **options)
    with connect(dest) as connection:
        _backup(wpsyncdir, dest, connection,
                arguments['--verbose'], **options)
        _rollback(wpsyncdir, source, dest, connection, backup_id,
                  arguments['--verbose'], **options)


def backup():
    assert_site_exists(config, arguments['<source>'])
    site = config[arguments['<source>']]
    with connect(site) as connection:
        _backup(wpsyncdir, site, connection, arguments['--verbose'], **options)


def rollback():
    source_site = None
    dest_site = None
    match = None
    backup_id = None

    # TODO would it make sense to make it work, too, if the given
    # --backup is *only* a site name (no timestamp) (and --site is
    # also give, of course?) - we could use the last backup from
    # the --backup site, then ...

    # if the --site argument is given, the user wanted it to be
    # the backup destination.
    if arguments['--site']:
        assert_site_exists(config, arguments['--site'])
        dest_site = config[arguments['--site']]

    # if the --backup argument is given, the user wanted the
    # backup with this particular id (and, optionally, from that
    # particular source) to be rolled back.
    if arguments['--backup']:
        match = re.match(r'(.+@)?(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',
                         arguments['--backup'])
        if not match:
            print('Wrong backup id format.'
                  ' It should look like [site@]yyyy-mm-ddThh:mm:ss')
            sys.exit(1)
        backup_id = match[2]

    # if neither of --site and --backup are given, or --site is not
    # given and the backup doesn't have the [site@] part, we can't
    # determine which site to rollback to!
    if not dest_site and (not match or not match[1]):
        print('You must, at least, either provide a fully qualified'
              ' backup id, or a site name')
        sys.exit(1)

    # if the dest_site wasn't given through the --site argument,
    # we'll determine it from the backup id - that means the backup
    # will be implicitly rolled back to the site it originally
    # belongs to.
    if not dest_site:
        dest_site_name = match[1][:-1]
        assert_site_exists(config, dest_site_name)
        dest_site = config[dest_site_name]

    # now let's determine the source site. if the backup_id has the
    # [site@] portion, we'll use this as the source. if not, we'll
    # use the same as the dest_site (given as --site).
    if match and match[1]:
        source_site_name = match[1][:-1]
        assert_site_exists(config, source_site_name)
        source_site = config[source_site_name]
    else:
        source_site = dest_site

    # finally, if no backup_id is given, we'll try to use the last
    # backup that was taken from the source site.
    if not backup_id:
        backup_dir = wpsyncdir / 'backups' / source_site['fs_safe_name']
        try:
            backup_id = sorted([b.name for b in backup_dir.iterdir()])[-1]
        except FileNotFoundError as e:
            print(f'There are no backups for {source_site["name"]}')
            sys.exit(1)
    # and if the backup_id came from the command line, we'll
    # convert it to the filesystem-safe version.
    else:
        backup_id = backup_id.replace(':', '_')

    # if no options are set, detect and use the options from the
    # backup we're going to roll back.
    if not any(options.values()):
        backup_dir = (wpsyncdir / 'backups' / source_site['fs_safe_name'] /
                      backup_id)
        options['database'] = (backup_dir / 'database').is_dir()
        options['uploads'] = (backup_dir / 'uploads').is_dir()
        options['plugins'] = (backup_dir / 'plugins').is_dir()
        options['themes'] = (backup_dir / 'themes').is_dir()
        options['full'] = (backup_dir / 'full').is_dir()

    with connect(dest_site) as connection:
        _rollback(wpsyncdir, source_site, dest_site, connection, backup_id,
                  arguments['--verbose'], **options)


def list_backups():
    if arguments['--site'] is not None:
        assert_site_exists(config, arguments['--site'])
        site_name = arguments['--site']
        site_names = [(site_name, config[site_name]['fs_safe_name'])]
    else:
        site_names = [(site, config[site]['fs_safe_name'])
                      for site
                      in config.keys()]
    _list_backups(wpsyncdir, site_names, **options)


def install():
    assert_site_exists(config, arguments['<site>'])
    site = config[arguments['<site>']]
    with connect(site) as connection:
        _install(site, connection, arguments['--verbose'])


if __name__ == '__main__':
    for executable_name in ['cat', 'lftp', 'rsync', 'ssh', 'scp']:
        check_required_executable(executable_name)
    arguments = docopt(__doc__, version='PyWpsync 0.0.0')
    (config, config_path) = get_config(arguments['--config'])
    wpsyncdir = get_wpsyncdir(config_path)
    options = get_options(arguments)

    if arguments['--legacy']:
        new_config = {}
        for site in config:
            new_config[config[site]['name']] = config[site]
            del config[site]['name']
        config = new_config

    for site in config:
        config[site]['name'] = site
        config[site]['fs_safe_name'] = encode_site_name(site)

    if arguments['sync']:
        sync()
    elif arguments['backup']:
        backup()
    elif arguments['rollback']:
        rollback()
    elif arguments['list']:
        list_backups()
    elif arguments['install']:
        install()
