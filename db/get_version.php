<?php
include("get_connection.php");

$sql = "SELECT version FROM version";

$pdo = get_connection();
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$stmt = $pdo->prepare($sql);
$stmt->execute([]);
$response = $stmt->fetchAll();

echo $response[0][0];
?>
