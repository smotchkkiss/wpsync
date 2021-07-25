<?php

$commands = [];

function wpsync_respond(string $command, callable $callback) {
    global $commands;
    $commands[$command] = $callback;
}

function wpsync_run() {
    global $commands;

    if (!isset($_POST['password'])) {
        http_response_code(500);
        echo "PASSWORD MISSING" and die();
    }

    if (!isset($_POST['command'])) {
        http_response_code(500);
        echo "COMMAND MISSING" and die();
    }

    if (!password_verify($_POST['password'], WPSYNC_PASSWORD_HASH)) {
        http_response_code(500);
        echo "WRONG PASSWORD" and die();
    }

    // TODO remove
    echo "RIGHT PASSWORD\n";
    die();

    if (!isset($commands[$_POST['command']])) {
        http_response_code(500);
        echo "UNKNOWN COMMAND" and die();
    }

    if (
        !isset($_POST['db_host']) ||
        !isset($_POST['db_port']) ||
        !isset($_POST['db_user']) ||
        !isset($_POST['db_pass']) ||
        !isset($_POST['db_name'])
    ) {
        http_response_code(500);
        echo "DB CREDENTIALS MISSING OR INCOMPLETE" and die();
    }

    if (!isset($_POST['dump_file_name'])) {
        http_response_code(500);
        echo "MISSING dump_file_name" and die();
    }

    $commands[$_POST['command']]();
}


// *** BACKUP ***
wpsync_respond('backup', function() {

    try {

        $connect_string = "mysql:host={$_POST['db_host']};";
        $connect_string .= "dbname={$_POST['db_name']};";
        $connect_string .= "port={$_POST['db_port']}";

        $dump = new Ifsnop\Mysqldump\Mysqldump(
            $connect_string,
            $_POST['db_user'],
            $_POST['db_pass'],
            [
                'extended-insert' => false,
                'add-drop-table' => true,
                // TODO only include tables w/ prefix
                // 'include-tables' => [],
            ]
        );

        $dump->start(__DIR__ . '/' . $_POST['dump_file_name']);

    } catch (Exception $e) {

        http_response_code(500);
        echo $e->getMessage();
    }

});


// *** RESTORE ***
wpsync_respond('restore', function() {

    if (!isset($_POST['search'])) {
        http_response_code(500);
        echo "MISSING search STRING" and die();
    }

    if (!isset($_POST['replace'])) {
        http_response_code(500);
        echo "MISSING replace STRING" and die();
    }

    try {

        IMPORT_TABLES(
            $_POST['db_host'],
            $_POST['db_user'],
            $_POST['db_pass'],
            $_POST['db_name'],
            $_POST['db_port'],
            __DIR__ . '/' . $_POST['dump_file_name']
        );

    } catch (Exception $e) {

        http_response_code(500);
        echo $e->getMessage();
    }

    ob_start();
    $report = new icit_srdb([
        'verbose' => true,
        'dry_run' => false,
        'host' => $_POST['db_host'],
        'name' => $_POST['db_name'],
        'user' => $_POST['db_user'],
        'pass' => $_POST['db_pass'],
        'port' => $_POST['db_port'],
        'search' => $_POST['search'],
        'replace' => $_POST['replace'],
        // TODO only include tables w/ prefix
        // 'tables' => [],
    ]);
    $output = ob_get_clean();

    if (!$report || !empty($report->errors['results'])) {

        http_response_code(500);
        if (!$report) {
            echo "The search-replace-database-tool didn't return a report.\n";
        }

        if (!empty($report->errors['results'])) {
            foreach ($report->errors['results'] as $error) {
                echo "$error\n";
            }
        }
    }
});


wpsync_run();
