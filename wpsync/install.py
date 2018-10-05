import put


# curly braces in php template are doubled to escape them
# (otherwise python will interpret them as replacement field
# delimiters)
wpinstall_php_template = '''<?php

$wp_path = realpath(__DIR__ . '/..');

// download WordPress
$localpath = __DIR__ . '/latest.zip';
$download = fopen('https://wordpress.org/latest.zip', 'r');
file_put_contents($localpath, $download);

// unzip it
$zip = new ZipArchive;
$is_zip_open = $zip->open($localpath);
if ($is_zip_open === TRUE) {{
    $zip->extractTo($wp_path);
    $zip->close();
}} else {{
    exit_with_error();
}}

// move to root
rmove($wp_path . '/wordpress', $wp_path);

// create wp-config.php
$wp_config_sample_path = $wp_path . '/wp-config-sample.php';
$wp_config_path = $wp_path . '/wp-config.php';
$wp_config = file_get_contents($wp_config_sample_path);
if ($wp_config === FALSE) {{
    exit_with_error();
}}

// database configuration
$wp_config = str_replace('database_name_here', '{mysql_name}', $wp_config);
$wp_config = str_replace('username_here', '{mysql_user}', $wp_config);
$wp_config = str_replace('password_here', '{mysql_pass}', $wp_config);
$wp_config = str_replace('localhost', '{mysql_host}', $wp_config);

// generate salts
$salt = file_get_contents('https://api.wordpress.org/secret-key/1.1/salt/');
if ($salt === FALSE) {{
    exit_with_error();
}}
$wp_config_lines = explode("\n", $wp_config);
$salt_start_line = "define('AUTH_KEY',";
$salt_start_line_number = 0;
foreach ($wp_config_lines as $index => $line) {{
    if (starts_with($line, $salt_start_line)) {{
        $salt_start_line_number = $index;
        break;
    }}
}}
$salt_lines = explode("\n", $salt);
$salt_length = sizeof($salt_lines);
array_splice(
    $wp_config_lines,
    $salt_start_line_number,
    $salt_length,
    $salt_lines
);
$wp_config = implode("\n", $wp_config_lines);

// replace all newlines with a default unix \n
$wp_config = preg_replace('~\R~u', "\n", $wp_config);

// set debug to true
$wp_config = str_replace(
    "define('WP_DEBUG', false);",
    "define('WP_DEBUG', true);",
    $wp_config
);

// write to file
$success = file_put_contents($wp_config_path, $wp_config);
if ($success === FALSE) {{
    exit_with_error();
}}

// remove latest.zip
unlink($localpath);

// DONE -- utilities:
function exit_with_error () {{
    $protocol = $_SERVER['SERVER_PROTOCOL'];
    $error_message = $protocol . ' 500 Internal Server Error';
    header($error_message, true, 500);
    exit();
}}

/**
  * Recursively move files from one directory to another
  *
  * Stolen from Ben Lobaugh:
  * https://ben.lobaugh.net/blog/864/php-5-recursively-move-or-copy-files
  *
  * But I removed the first `unlink` line because the directory
  * will already be removed at that point so there's no need to
  * remove it again and I replaced the second `unlink` with `rmdir`
  * since unlink is not allowed on directories.
  *
  * @param String $src - Source of files being moved
  * @param String $dest - Destination of files being moved
  */
function rmove($src, $dest) {{

    // If source is not a directory stop processing
    if(!is_dir($src)) return false;

    // If the destination directory does not exist create it
    if(!is_dir($dest)) {{
        if(!mkdir($dest)) {{
            // If the destination directory could not be created stop processing
            return false;
        }}
    }}

    // Open the source directory to read in files
    $i = new DirectoryIterator($src);
    foreach($i as $f) {{
        if($f->isFile()) {{
            rename($f->getRealPath(), "$dest/" . $f->getFilename());
        }} else if(!$f->isDot() && $f->isDir()) {{
            rmove($f->getRealPath(), "$dest/$f");
        }}
    }}
    rmdir($src);
}}

// https://stackoverflow.com/a/834355
function starts_with ($haystack, $needle) {{
    $length = strlen($needle);
    return (substr($haystack, 0, $length) === $needle);
}}
'''


def install(site, connection, quiet):
    if not quiet:
        put.title(f'Installing new WordPress for {site["name"]}')
    # TODO:
    # check if there's already a WordPress at the site, and if so,
    # ask the user if they want to replace it.
    php_code = wpinstall_php_template.format(**site)
    connection.run_php(php_code)
