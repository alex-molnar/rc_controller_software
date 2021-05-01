<?php
include("passwd.php");

$version = $_POST["version"];

$sql = "UPDATE version SET version=:version";
$params = ["version" => $version];

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->prepare($sql)->execute($params);

?>
