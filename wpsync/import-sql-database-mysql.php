<?php	  
// EXAMPLE: IMPORT_TABLES("localhost","user","pass","db_name", "my_baseeee.sql"); //TABLES WILL BE OVERWRITTEN
// P.S. IMPORTANT NOTE for people who try to change/replace some strings in SQL FILE before importing, MUST READ: https://goo.gl/2fZDQL

// https://github.com/tazotodua/useful-php-scripts 
function IMPORT_TABLES($host,$user,$pass,$dbname,$port, $sql_file_path) {
    set_time_limit(3000);
    $handle = fopen($sql_file_path, 'r');

    if (!$handle) {
        echo "Failed to open {$sql_file_path}\n";
        return;
    }

    $mysqli = new mysqli($host, $user, $pass, $dbname, $port);
    if (mysqli_connect_errno()) {
        echo 'Failed to connect to MySQL: ' . mysqli_connect_error() . "\n";
        return;
    }

    $mysqli->query("SET NAMES 'utf8'");
    $templine = '';	// Temporary variable, used to store current query

    while (($line = fgets($handle)) !== false) {
        if (substr($line, 0, 2) != '--' && $line != '') {
            $templine .= $line; // (if it is not a comment..) Add this line to the current segment
            if (substr(trim($line), -1, 1) == ';') { // If it has a semicolon at the end, it's the end of the query
                if (!$mysqli->query($templine)) {
                    print('Error performing query \'<strong>' . $templine . '\': ' . $mysqli->error . '<br /><br />' . "\n");
                }
                $templine = ''; // set variable to empty, to start picking up the lines after ";"
            }
        }
    }
    return 'Importing finished. Now, Delete the import file.';
}
