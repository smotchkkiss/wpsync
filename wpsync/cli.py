"""wpsync

Synchronise WordPress sites across ssh, (s)ftp and local hosts

Usage:
  wpsync [-q] [-c file] [-l] (sync|s) ((-d|-u|-p|-t)... | -a | -f) <source> <dest>
  wpsync [-q] [-c file] [-l] (backup|b) ((-d|-u|-p|-t)... | -a | -f) <source>
  wpsync [-q] [-c file] [-l] (restore|r) [(-d|-u|-p|-t)... | -a | -f] [-b backup] [-s site]
  wpsync [-q] [-c file] [-l] (list|l) [(-d|-u|-p|-t)... | -a | -f] [-s site]
  wpsync [-q] [-c file] [-l] (install|i) <site>
  wpsync -h | --help
  wpsync -V | --version

Arguments:
  source  Name of a WordPress site from your config file
  dest    Name of a WordPress site from your config file
  site    Name of a WordPress site from your config file

Options:
  -h --help                  Output usage information.
  -V --version               Output version number.
  -q --quiet                 Don't print anything to STDOUT.
  -c file --config=file      Use the config file specified.
  -l --legacy                Use old name field instead of config section headers.
  -b backup --backup=backup  ID of a specific backup to use.
  -s site --site=site        Specify a site where it's optional.
  -d --database              Sync/Backup/Restore database.
  -u --uploads               Sync/Backup/Restore uploads.
  -p --plugins               Sync/Backup/Restore plugins.
  -t --themes                Sync/Backup/Restore the themes.
  -a --all                   Sync/Backup/Restore all of the above.
  -f --full                  Sync/Backup/Restore the full site.
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
from rollback import restore as _restore
from list_backups import list_backups as _list_backups
from install import install as _install
import put


# TODO:
# - make the --full option work; auto-adapt wp-config.php
# - on connect, check if a WordPress actually exists at the site,
#   and if not, maybe ask if the user wants to install one?
# - don't crash if the wpsync dir already exists on connect, and
#   generally be generous with existing/non-existing directories
# - maybe even add a 'default' section to config where a username
#   and password can be specified that will be used for new
#   installations?
# - check: did I actually implement maintenance mode? maintenance
#   mode should be on, at least during database restore - better
#   during all backup and restore activities!
# - drop support for the 'theme' config key, it was a bad idea
# - support databases with multiple installations or other stuff
#   than wordpress in them, add an optional 'mysql_prefix'
#   configuration option for that
# - unify all php code together into one client.php so we only have
#   to upload it once on connect
# - maybe add an option to persistently install the client? (no!)
# - make the client safer by using http simple auth with
#   automatically, per-connection generated passwords
# - support a new 'alias' configuration option for shorter,
#   alternative site names for easier command line use
# - would it somehow be possible to make [site] an optional
#   argument to restore (and not an option?)
# - publish to PyPI and/or, preferably, homebrew!
# - maybe refactor here and there for more consistent variable
#   names (backup_id vs ts_fs, source_site and dest_site vs source
#   and dest)
#   refactor for less [positional] arguments
# - check that we're running on the right python version (that
#   would be 3.6+ I guess?) at startup
# - check that we check that the local peer dependencies are
#   installed (lftp and so on!) - or even better, maybe we can
#   define those as dependencies in the homebrew formula? (but
#   anyway, still check for them programmatically, please!)
# - if things get too complex, maybe drop support for native
#   mysql/mysqldump and focus on the PHP version, which should
#   work everywhere!
# - maybe update the PHP dependencies
# - add support for (project-)local configuration files and local
#   'wpsyncdir's in the respective location(s) - or find a way to
#   uniquely identify sites, for example by base_url (or a
#   filesystem-safe version of that), or a combination of the site
#   name and the path of the configuration file it belongs to ...
# - normalise config options like base_url to make sure they don't
#   have a trailing slash or trailing whitespace for example, or
#   hint the user towards it!
# - generally validate the config better
# - randomise the server side dir name for better security (but
#   make sure to remove it!)
# - what if more people are syncing the same site at the same time?
#   add individual ids or detect the other folders, e.g. by a
#   common ('wpsync-') prefix, so only the last one leaving removes
#   the maintenance file?
#   or maybe better, do nothing and wait until the others are
#   done - this may wait forever in case a wpsync dir is left over
#   from a crash! we should warn the user about this and advise how
#   to manually remove the old wpsync directories.
# - add a 'clean' command or something to remove old backups
# - add another 'clean' command that removes old wpsync dirs from
#   servers
# - but by all means try to remove the wpsync dir, maybe with a
#   python atexit hook or something that will run in almost every
#   case except for power outage or sudden connection loss or
#   something ... and in case of the connection loss, maybe still
#   write the name of the wpsync dir to a list of stale wpsync dirs
#   in the host info file so we know we can remove it next time?
# - maybe change the restore cli to [backup] [site] and, if both
#   are given, try to detect if [backup] is a backup_id or a site,
#   and so on ... ?
# - add waiting spinners on steps?
# - maybe add a verbose option again and make it show very verbose
#   output of lftp, rsync and other external tools
# - parallelise stuff, probably with asyncio
# - test wether everything works over each connection type
# - require particular (min/max?) versions of external dependencies
#   (like lftp and so on) and check that compatible versions are
#   installed. (if wpsync is published to homebrew they may even be
#   listed in the formula and installed automatically, but I think
#   that it has to be the latest version available on homebrew,
#   then.)
# - detect when a host uses http auth but it isn't configured
#   (401 Unauthorized) and show a meaningful error message
# - don't just print DONE at the end of the program, especially if
#   there were errors, and it also makes no sense with the list
#   command _at all_ I think.
# - compress backups
# - add a --only-files option to --full, or think of a better way,
#   but make it possible to explicitly include/exclude the database
# - also add an option to --full about wether to include or exclude
#   the .htaccess file (when syncing to another site)
# - or are the above 2 points a case of YAGNI and we can just go
#   with some default and in the rare cases where we need more
#   options we just do it by hand?
# - handle exit via KeyboardInterrupt more gracefully
# - make it possible to restore -dupt selectively from a --full
#   backup
# - rename rollback.py to restore.py
# - zip directories on remote hosts before downloading them, also
#   upload zips and restore them there


def sync():
    assert_site_exists(config, arguments['<source>'])
    assert_site_exists(config, arguments['<dest>'])
    source = config[arguments['<source>']]
    dest = config[arguments['<dest>']]
    with connect(source) as connection:
        backup_id = _backup(wpsyncdir, source, connection,
                            arguments['--quiet'], **options)
    with connect(dest) as connection:
        _backup(wpsyncdir, dest, connection,
                arguments['--quiet'], **options)
        _restore(wpsyncdir, source, dest, connection, backup_id,
                 arguments['--quiet'], **options)


def backup():
    assert_site_exists(config, arguments['<source>'])
    site = config[arguments['<source>']]
    with connect(site) as connection:
        _backup(wpsyncdir, site, connection, arguments['--quiet'], **options)


def restore():
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
            put.error('Wrong backup id format.'
                      ' It should look like [site@]yyyy-mm-ddThh:mm:ss')
            sys.exit(1)
        backup_id = match[2]

    # if neither of --site and --backup are given, or --site is not
    # given and the backup doesn't have the [site@] part, we can't
    # determine which site to restore to!
    if not dest_site and (not match or not match[1]):
        put.error('You must, at least, either provide a fully qualified'
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
            put.error(f'There are no backups for {source_site["name"]}')
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
        _restore(wpsyncdir, source_site, dest_site, connection, backup_id,
                 arguments['--quiet'], **options)


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
        _install(site, connection, arguments['--quiet'])


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

    if arguments['sync'] or arguments['s']:
        sync()
    elif arguments['backup'] or arguments['b']:
        backup()
    elif arguments['restore'] or arguments['r']:
        restore()
    elif arguments['list'] or arguments['l']:
        list_backups()
    elif arguments['install'] or arguments['i']:
        install()

    if not arguments['--quiet']:
        put.success('DONE')
