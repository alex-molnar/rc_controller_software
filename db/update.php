<?php
include("passwd.php");

$id = $_GET["id"];
$ip = $_GET["ip"];
$port = $_GET["port"];
$ssid = $_GET["ssid"];
$available = $_GET["available"] ? $_GET["available"] : 0;

$sql = "UPDATE rc_connection SET ip=INET_ATON(:ip), port=:port, ssid=:ssid, available=:available, time_stamp=:time_stamp WHERE id=:id";
$params = ["ip" => $ip, "port" => $port, "ssid" => $ssid, "available" => $available, "id" => $id, "time_stamp" => date("Y-m-d H:i:s")];

$pdo = new PDO("mysql:host=mysql.caesar.elte.hu;dbname=kingbrady", "kingbrady", get_password());
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->prepare($sql)->execute($params);

?>
