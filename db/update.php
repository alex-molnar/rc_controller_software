<?php
include("passwd.php");

$id = $_POST["id"];
$name = $_POST["name"];
$ip = $_POST["ip"];
$port = $_POST["port"];
$ssid = $_POST["ssid"];
$available = $_POST["available"] ? $_POST["available"] : 0;

$sql = "UPDATE rc_connection SET name=:name, ip=INET_ATON(:ip), port=:port, ssid=:ssid, available=:available, time_stamp=:time_stamp WHERE id=:id";
$params = [
    "ip" => $ip,
    "name" => $name,
    "port" => $port,
    "ssid" => $ssid,
    "available" => $available,
    "id" => $id,
    "time_stamp" => date("Y-m-d H:i:s")
];

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->prepare($sql)->execute($params);

?>
