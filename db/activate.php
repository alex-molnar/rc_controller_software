<?php
include("passwd.php");

$id = $_GET["id"];

$sql = "UPDATE rc_connection SET available=1 WHERE id=:id";
$params = ["id" => $id];

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->prepare($sql)->execute($params);

?>
