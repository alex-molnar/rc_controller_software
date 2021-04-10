<?php
include("passwd.php");

$name = $_POST["name"];
$unique_auth_key = $_POST["key"];

$sql = "INSERT INTO rc_connection(name, unique_auth_key) VALUES (:name, :key)";
$params = ["name" => $name, "key" => $unique_auth_key];  // , "time_stamp" => date("Y-m-d H:i:s)

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->prepare($sql)->execute($params);
?>
