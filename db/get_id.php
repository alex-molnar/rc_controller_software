<?php
include("passwd.php");

$unique_auth_key = $_GET["key"];

$sql = "SELECT id FROM rc_connection WHERE unique_auth_key=:key";
$params = ["key" => $unique_auth_key];

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$response = $stmt->fetchAll();

if(count($response) > 0) {
    $sql = "UPDATE rc_connection SET unique_auth_key=null WHERE id=:id";
    $params = ["id" => $response[0][0]];
    $stmt = $pdo->prepare($sql)->execute($params);
}

echo $response[0][0];
?>
