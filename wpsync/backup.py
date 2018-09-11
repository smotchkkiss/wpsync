from datetime import datetime
from pathlib import Path
from host_info import HostInfo


this_dir = Path(__file__).resolve().parent
mysqldump_php_template = '''<?php

include_once(__DIR__ . '/Mysqldump.php');

try {{

    $dump = new Ifsnop\Mysqldump\Mysqldump(
        'mysql:host={mysql_host};dbname={mysql_name}',
        '{mysql_user}',
        '{mysql_pass}',
        array(
            'extended-insert' => false,
            'add-drop-table' => true,
        )
    );

    $dump->start(__DIR__ . '/dump.sql');

}} catch (Exception $e) {{

    http_response_code(500); # internal server error
    echo $e->getMessage();
}}
'''


def backup(wpsyncdir, site, connection, verbose,
           database, uploads, plugins, themes, full):
    host = HostInfo(wpsyncdir, site, connection)
    dt = datetime.now()
    print_dt = str(dt)[:19]
    iso_ts = dt.isoformat()[:19]
    fs_ts = f'{iso_ts[:13]}_{iso_ts[14:16]}_{iso_ts[17:]}'
    backup_dir = wpsyncdir / 'backups' / site['fs_safe_name'] / fs_ts

    if verbose:
        print(f'Creating new backup for {site["name"]} on {print_dt}')

    if database:
        if verbose:
            print('Backing up database ... ', end='', flush=True)
        database_backup_dir = backup_dir / 'database'
        local_dump_file = database_backup_dir / 'dump.sql'
        remote_dump_file = connection.normalise('dump.sql')
        database_backup_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        if host.has_executable('mysqldump'):
            connection.shell(
                'mysqldump',
                '--skip-extended-insert',
                '--quick',
                '--default-character-set=utf8',
                '-r',
                remote_dump_file,
                site['mysql_name']
            )
        else:
            php_code = mysqldump_php_template.format(**site)
            mysqldump_library_local = this_dir / 'Mysqldump.php'
            mysqldump_library_remote = connection.normalise('Mysqldump.php')
            connection.put(mysqldump_library_local, mysqldump_library_remote)
            connection.run_php(php_code)
            connection.rm(mysqldump_library_remote)
        connection.get(remote_dump_file, local_dump_file)
        connection.rm(remote_dump_file)
        if verbose:
            print('DONE')

    if uploads:
        backup_a_dir(backup_dir, site, connection, 'uploads', verbose)

    if plugins:
        backup_a_dir(backup_dir, site, connection, 'plugins', verbose)

    if themes:
        backup_a_dir(backup_dir, site, connection, 'themes', verbose)

    return fs_ts


def backup_a_dir(backup_dir, site, connection, name, verbose):
    if verbose:
        print(f'Backing up {name} ... ', end='', flush=True)
    local_dir = backup_dir / name
    remote_dir = f'{site["base_dir"]}/wp-content/{name}'
    if not connection.dir_exists(remote_dir):
        if verbose:
            print(f'\bwp-content/{name} doesn\'t exist on {site["name"]},' +
                  ' creating it')
        connection.mkdir(remote_dir)
    local_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
    connection.mirror(remote_dir, local_dir)
    if verbose:
        print('DONE')
