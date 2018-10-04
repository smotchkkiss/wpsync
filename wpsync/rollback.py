import sys
from tempfile import NamedTemporaryFile
from pathlib import Path
from shlex import quote
import sqlparse
from host_info import HostInfo


this_dir = Path(__file__).resolve().parent
mysqlsource_php_template = '''<?php

include_once(__DIR__ . '/import-sql-database-mysql.php');

try {{

    IMPORT_TABLES(
        '{mysql_host}',
        '{mysql_user}',
        '{mysql_pass}',
        '{mysql_name}',
        __DIR__ . '/dump.sql'
    );

}} catch (Exception $e) {{

    http_response_code(500);
    echo $e->getMessage();
}}
'''


mysqlreplace_php_template = '''<?php

require_once(__DIR__ . '/srdb.class.php');

ob_start();
$report = new icit_srdb(array(
    'verbose' => true,
    'dry_run' => false,
    'host' => '{mysql_host}',
    'name' => '{mysql_name}',
    'user' => '{mysql_user}',
    'pass' => '{mysql_pass}',
    'search' => '{search}',
    'replace' => '{replace}',
));
$output = ob_get_clean();

if (!$report || !empty($report->errors['results'])) {{

    http_response_code(500);
    print_r($report->errors);
    echo $output;
}}
'''


def rollback(wpsyncdir, source, dest, connection, fs_ts, verbose,
             database, uploads, plugins, themes, full):
    host = HostInfo(wpsyncdir, dest, connection)
    backup_dir = wpsyncdir / 'backups' / source['fs_safe_name'] / fs_ts

    if database:
        rollback_database(source, dest, connection, backup_dir, host, verbose)

    if uploads:
        rollback_a_dir(backup_dir, dest, connection, 'uploads', verbose)

    if plugins:
        rollback_a_dir(backup_dir, dest, connection, 'plugins', verbose)

    if themes:
        rollback_a_dir(backup_dir, dest, connection, 'themes', verbose)


def rollback_database(source, dest, connection, backup_dir, host, verbose):
    dump_file = backup_dir / 'database' / 'dump.sql'
    if not dump_file.is_file():
        print('Database is not contained in this backup')
        return
    if verbose:
        print('Rolling back database ... ', end='', flush=True)

    if dest != source:
        if verbose:
            print('\nRollback source and target are different sites -'
                  '\nAltering database dump to match target settings')
        try:
            db_settings = host.get_database_settings()
        except RuntimeError as e:
            print(f'Error: {e}')
            print(f'Create a backup for {dest["name"]} first!')
            sys.exit(1)
        temp_dump_file = Path(NamedTemporaryFile().name)
        replace_in_database_dump(dump_file, temp_dump_file, db_settings)

        # use modified dump for import
        dump_file = temp_dump_file

    remote_dump_file = connection.normalise('dump.sql')
    connection.put(dump_file, remote_dump_file)

    php_code = mysqlsource_php_template.format(**dest)
    mysqlimport_library_local = this_dir / 'import-sql-database-mysql.php'
    mysqlimport_library_remote = connection.normalise(
        'import-sql-database-mysql.php'
    )
    connection.put(mysqlimport_library_local, mysqlimport_library_remote)
    connection.run_php(php_code)
    connection.rm(mysqlimport_library_remote)

    connection.rm(remote_dump_file)

    if 'temp_dump_file' in locals():
        temp_dump_file.unlink()

    if dest != source:
        if verbose:
            print('Replacing urls in the database')
        # TODO:
        # escape quotes in all strings formatted into php
        # templates!
        php_code = mysqlreplace_php_template.format(
            search=source['base_url'], replace=dest['base_url'], **dest)
        mysqlreplace_library_local = this_dir / 'srdb.class.php'
        mysqlreplace_library_remote = connection.normalise('srdb.class.php')
        connection.put(mysqlreplace_library_local, mysqlreplace_library_remote)
        connection.run_php(php_code)
        connection.rm(mysqlreplace_library_remote)

    if verbose:
        print('DONE')


def rollback_a_dir(backup_dir, dest, connection, name, verbose):
    if verbose:
        print(f'Rolling back {name} ... ', end='', flush=True)
    local_dir = backup_dir / name
    if dest['base_dir']:
        base = dest['base_dir'] + '/'
    else:
        base = ''
    remote_dir = f'{base}wp-content/{name}'
    if not connection.dir_exists(remote_dir):
        if verbose:
            print(f'\nwp-content/{name} doesn\'t exist on {dest["name"]},' +
                  ' creating it')
        connection.mkdir(remote_dir)
    connection.mirror_r(local_dir, remote_dir)
    if verbose:
        print('DONE')


def replace_in_database_dump(in_file, out_file, to_set):
    db_dump = in_file.read_text(encoding='utf-8')
    statements = sqlparse.parse(db_dump)
    detected_keyword = None
    serialised = []
    detected_collate = False
    for statement in statements:

        # only look at CREATE statements to replace values in
        if statement.token_first().value == 'CREATE':
            for token in statement.flatten():
                if token.value in to_set:
                    detected_keyword = token.value
                elif (detected_keyword and
                      token.ttype == sqlparse.tokens.Token.Name):
                    token.value = to_set[detected_keyword]
                    detected_keyword = None

                # if COLLATE is not in to_set, we want to remove
                # COLLATE definitions from the dump
                # so we delete all token values from here up to
                # and including the next sqlparse.tokens.Token.Name
                # TODO this leaves trailing whitespace in some places
                # in the modified dump file which works but doesn't
                # seem like a clean solution
                elif token.value == 'COLLATE':
                    detected_collate = True
                    token.value = ''
                elif (detected_collate and
                      token.ttype != sqlparse.tokens.Token.Name):
                    token.value = ''
                elif (detected_collate and
                      token.ttype == sqlparse.tokens.Token.Name):
                    token.value = ''
                    detected_collate = False

        serialised.append(str(statement))

    modified_db_dump = ''.join(serialised)
    out_file.write_text(modified_db_dump, encoding='utf-8')
