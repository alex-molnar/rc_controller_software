<?php
include("get_connection.php");

$id = $_POST["id"];

$sql = "UPDATE rc_connection SET available=0, time_stamp=:time_stamp WHERE id=:id";
$params = ["id" => $id, "time_stamp" => date("Y-m-d H:i:s")];

$pdo = get_connection();
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->prepare($sql)->execute($params);

?>
