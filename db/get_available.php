<?php
include("passwd.php");

function is_available($var)
{
    return $var["available"] == 1;
}

$sql = "SELECT INET_NTOA(`ip`) ip, port, ssid, available FROM rc_connection";

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$stmt = $pdo->prepare($sql);
$stmt->execute([]);
$response = $stmt->fetchAll();

header('Content-Type: application/json');
echo json_encode(array_values(array_filter($response, "is_available")));
?>
