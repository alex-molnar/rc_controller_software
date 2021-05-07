<?php
function get_connection(){
    $file = fopen("connection.json", "r");
    $connection_string = fread($file,filesize("connection.json"));
    fclose($file);
    $connection_data = json_decode($connection_string);
    return new PDO($connection_data->url, $connection_data->username, $connection_data->passwd);
}
