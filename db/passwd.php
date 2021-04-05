<?php
function get_password(){
    $passwd_file = fopen("passwd", "r");
    $passwd = fread($passwd_file,filesize("passwd"));
    fclose($passwd_file);
    return $passwd;
}