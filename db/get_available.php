<?php
include("get_connection.php");

function is_available($var)
{
    return $var["available"] == 1;
}

$sql = "SELECT INET_NTOA(`ip`) ip, port, ssid, available, time_stamp FROM rc_connection";

$pdo = get_connection();
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$stmt = $pdo->prepare($sql);
$stmt->execute([]);
$response = $stmt->fetchAll();

header('Content-Type: application/json');
echo json_encode(array_values(array_filter($response, "is_available")));
?>
