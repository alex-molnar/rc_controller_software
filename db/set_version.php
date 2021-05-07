<?php
include("get_connection.php");

$version = $_POST["version"];

$sql = "UPDATE version SET version=:version";
$params = ["version" => $version];

$pdo = get_connection();
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->prepare($sql)->execute($params);

?>
