import os
from datetime import datetime
from host_info import HostInfo


this_dir = os.path.dirname(os.path.realpath(__file__))
mysqldump_php_template = '''<?php

include_once(__DIR__ . '/Mysqldump.php');

try {

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

} catch (Exception $e) {

    # try to write the error message to a file so we can
    # read it. no need to check the return value, though --
    # we're returning a 500 anyways ...
    file_put_contents(__DIR__ . '/error.txt', $e->getMessage());

    http_response_code(500); # internal server error
}
'''


def backup_a_dir(backup_dir, site, connection, name, wp_path):
    print(f'Backing up {name} ... ', end='', flush=True)
    local_dir = os.path.join(backup_dir, name)
    remote_dir = os.path.join(site['base_dir'], wp_path)
    if not connection.dir_exists(remote_dir):
        print(f'\n{wp_path} doesn\'t exist on {site["name"]}')
    else:
        os.makedirs(local_dir, mode=0o755, exist_ok=True)
        connection.mirror(remote_dir, local_dir)
    print('DONE')


def backup(wpsyncdir, site, connection, verbose,
           database, uploads, plugins, themes, full):

    host = HostInfo(wpsyncdir, site, connection)
    dt = datetime.now()
    print_dt = str(dt)[:19]
    iso_ts = dt.isoformat()[:19]
    fs_ts = f'{iso_ts[:13]}_{iso_ts[14:16]}_{iso_ts[17:]}'
    backup_dir = os.path.join(
        wpsyncdir,
        'backups',
        site['fs_safe_name'],
        fs_ts
    )

    print(f'Creating new backup for {site["name"]} on {print_dt}')

    if database:
        print('Backing up database ... ', end='', flush=True)
        database_backup_dir = os.path.join(backup_dir, 'database')
        local_dump_file = os.path.join(database_backup_dir, 'dump.sql')
        remote_dump_file = connection.normalise('dump.sql')
        os.makedirs(database_backup_dir, mode=0o755, exist_ok=True)
        if host.mysqldump:
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
            php_code = mysqldump_php_template.format(site)
            mysqldump_library_local = os.path.join(this_dir, 'Mysqldump.php')
            mysqldump_library_remote = connection.normalise('Mysqldump.php')
            connection.put(mysqldump_library_local, mysqldump_library_remote)
            connection.run_php(php_code)
            connection.rm(mysqldump_library_remote)
        connection.get(remote_dump_file, local_dump_file)
        connection.rm(remote_dump_file)
        print('DONE')

    if uploads:
        backup_a_dir(backup_dir, site, connection, 'uploads', 'wp-content/uploads')

    if plugins:
        backup_a_dir(backup_dir, site, connection, 'plugins', 'wp-content/plugins')

    if themes:
        wp_path = 'wp-content/themes'
        if 'theme' in site:
            wp_path = os.path.join(wp_path, site['theme'])
        backup_a_dir(backup_dir, site, connection, 'themes', wp_path)
