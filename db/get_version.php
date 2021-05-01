<?php
include("passwd.php");

$sql = "SELECT version FROM version";

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$stmt = $pdo->prepare($sql);
$stmt->execute([]);
$response = $stmt->fetchAll();

echo $response[0][0];
?>
