import sys
from tempfile import NamedTemporaryFile
from pathlib import Path
from shlex import quote
import re
import sqlparse
from .host_info import HostInfo
from . import put
from .connection import RemoteExecutionError


this_dir = Path(__file__).resolve().parent
mysqlsource_php_template = """<?php

include_once(__DIR__ . '/import-sql-database-mysql.php');

try {{

    IMPORT_TABLES(
        '{mysql_host}',
        '{mysql_user}',
        '{mysql_pass}',
        '{mysql_name}',
        {mysql_port},
        __DIR__ . '/dump.sql'
    );

}} catch (Exception $e) {{

    http_response_code(500);
    echo $e->getMessage();
}}
"""


mysqlreplace_php_template = """<?php

require_once(__DIR__ . '/srdb.class.php');

ob_start();
$report = new icit_srdb(array(
    'verbose' => true,
    'dry_run' => false,
    'host' => '{mysql_host}',
    'name' => '{mysql_name}',
    'user' => '{mysql_user}',
    'pass' => '{mysql_pass}',
    'port' => {mysql_port},
    'search' => '{search}',
    'replace' => '{replace}',
));
$output = ob_get_clean();

if (!$report || !empty($report->errors['results'])) {{

    http_response_code(500);
    if (!$report) {{
        echo "The search-replace-database-tool didn't return a report.\n";
    }}

    if (!empty($report->errors['results'])) {{
        foreach ($report->errors['results'] as $error) {{
            echo "$error\n";
        }}
    }}
}}
"""


def restore(
    wpsyncdir,
    source,
    dest,
    connection,
    fs_ts,
    quiet,
    database,
    uploads,
    plugins,
    themes,
    full,
):
    host = HostInfo(wpsyncdir, dest, connection)
    backup_dir = wpsyncdir / "backups" / source["fs_safe_name"] / fs_ts

    if not quiet:
        what = source["name"] + "@" + fs_ts.replace("_", ":")
        if source != dest:
            what += " to " + dest["name"]
        put.title(f"Restoring {what}")

    if database or full:
        restore_database(source, dest, connection, backup_dir, host, quiet)

    if uploads:
        restore_a_dir(backup_dir, dest, connection, "uploads", quiet)

    if plugins:
        restore_a_dir(backup_dir, dest, connection, "plugins", quiet)

    if themes:
        restore_a_dir(backup_dir, dest, connection, "themes", quiet)

    if full:
        if not quiet:
            put.step("Restoring full site")
        local_dir = backup_dir / "full"
        remote_dir = dest["base_dir"][:-1]
        exclude = []
        if dest != source:
            exclude.extend([".htaccess", "wp-config.php"])
        connection.mirror_r(local_dir, remote_dir, exclude=exclude)
        if dest != source:
            put.step("Adapting wp-config.php for target and uploading it")
            wp_config_file = local_dir / "wp-config.php"
            temp_wp_config_file = Path(NamedTemporaryFile().name)
            adapt_wp_config_php(wp_config_file, temp_wp_config_file, dest)
            remote_wp_config_file = remote_dir + "/wp-config.php"
            connection.put(temp_wp_config_file, remote_wp_config_file)
            put.step("Uploading default .htaccess")
            local_htaccess_file = this_dir / "htaccess-default.txt"
            remote_htacces_file = remote_dir + "/.htaccess"
            connection.put(local_htaccess_file, remote_htacces_file)


def restore_database(source, dest, connection, backup_dir, host, quiet):
    dump_file = backup_dir / "database" / "dump.sql"
    if not dump_file.is_file():
        put.error("Database is not contained in this backup")
        return
    if not quiet:
        put.step("Restoring database")

    if dest != source:
        if not quiet:
            put.info("Altering database dump to match target settings")
        try:
            db_settings = host.get_database_settings()
        except RuntimeError as e:
            put.error(
                f"Error: {e}" + f'\n  Create a backup for {dest["name"]} first!'
            )
            sys.exit(1)
        temp_dump_file = Path(NamedTemporaryFile().name)
        replace_in_database_dump(dump_file, temp_dump_file, db_settings)

        # use modified dump for import
        dump_file = temp_dump_file

    remote_dump_file = connection.normalise("dump.sql")
    connection.put(dump_file, remote_dump_file)

    php_code = mysqlsource_php_template.format(**dest)
    mysqlimport_library_local = this_dir / "import-sql-database-mysql.php"
    mysqlimport_library_remote = connection.normalise(
        "import-sql-database-mysql.php"
    )
    connection.put(mysqlimport_library_local, mysqlimport_library_remote)
    try:
        connection.run_php(php_code)
    except RemoteExecutionError as error:
        put.error(f"Error importing the SQL dump: {error}")
        return
    finally:
        connection.rm(mysqlimport_library_remote)
        connection.rm(remote_dump_file)

    if "temp_dump_file" in locals():
        temp_dump_file.unlink()

    if dest != source:
        if not quiet:
            put.step("Replacing urls in the database")
        # TODO:
        # escape quotes in all strings formatted into php
        # templates!
        php_code = mysqlreplace_php_template.format(
            search=source["site_url"], replace=dest["site_url"], **dest
        )
        mysqlreplace_library_local = this_dir / "srdb.class.php"
        mysqlreplace_library_remote = connection.normalise("srdb.class.php")
        connection.put(mysqlreplace_library_local, mysqlreplace_library_remote)
        try:
            connection.run_php(php_code)
        except RemoteExecutionError as error:
            put.error(error)
        finally:
            connection.rm(mysqlreplace_library_remote)


def restore_a_dir(backup_dir, dest, connection, name, quiet):
    if not quiet:
        put.step(f"Restoring {name}")
    local_dir = backup_dir / name
    remote_dir = f'{dest["base_dir"]}wp-content/{name}'
    if not connection.dir_exists(remote_dir):
        if not quiet:
            put.info(
                f'wp-content/{name} doesn\'t exist on {dest["name"]},'
                + " creating it"
            )
        connection.mkdir(remote_dir)
    connection.mirror_r(local_dir, remote_dir)


def replace_in_database_dump(in_file, out_file, to_set):
    db_dump = in_file.read_text(encoding="utf-8")
    statements = sqlparse.parse(db_dump)
    detected_keyword = None
    serialised = []
    detected_collate = False
    for statement in statements:

        # only look at CREATE statements to replace values in
        if statement.token_first().value == "CREATE":
            for token in statement.flatten():
                if token.value in to_set:
                    detected_keyword = token.value
                elif (
                    detected_keyword
                    and token.ttype == sqlparse.tokens.Token.Name
                ):
                    token.value = to_set[detected_keyword]
                    detected_keyword = None

                # if COLLATE is not in to_set, we want to remove
                # COLLATE definitions from the dump
                # so we delete all token values from here up to
                # and including the next sqlparse.tokens.Token.Name
                # TODO this leaves trailing whitespace in some places
                # in the modified dump file which works but doesn't
                # seem like a clean solution
                elif token.value == "COLLATE":
                    detected_collate = True
                    token.value = ""
                elif (
                    detected_collate
                    and token.ttype != sqlparse.tokens.Token.Name
                ):
                    token.value = ""
                elif (
                    detected_collate
                    and token.ttype == sqlparse.tokens.Token.Name
                ):
                    token.value = ""
                    detected_collate = False

        serialised.append(str(statement))

    modified_db_dump = "".join(serialised)
    out_file.write_text(modified_db_dump, encoding="utf-8")


def adapt_wp_config_php(in_file, out_file, site):
    wp_config = in_file.read_text(encoding="utf-8")
    wp_config = re.sub(
        r'define\s*\(\s*(\'|")DB_NAME\1\s*,\s*(\'|").*?\2\s*\)',
        f'define(\'DB_NAME\', \'{site["mysql_name"]}\')',
        wp_config,
    )
    wp_config = re.sub(
        r'define\s*\(\s*(\'|")DB_USER\1\s*,\s*(\'|").*?\2\s*\)',
        f'define(\'DB_USER\', \'{site["mysql_user"]}\')',
        wp_config,
    )
    wp_config = re.sub(
        r'define\s*\(\s*(\'|")DB_PASSWORD\1\s*,\s*(\'|").*?\2\s*\)',
        f'define(\'DB_PASSWORD\', \'{site["mysql_pass"]}\')',
        wp_config,
    )
    wp_config = re.sub(
        r'define\s*\(\s*(\'|")DB_HOST\1\s*,\s*(\'|").*?\2\s*\)',
        f'define(\'DB_HOST\', \'{site["mysql_host"]}\')',
        wp_config,
    )
    out_file.write_text(wp_config, encoding="utf-8")
