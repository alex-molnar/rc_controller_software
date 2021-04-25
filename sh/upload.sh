#!/usr/bin/expect -f


set prompt ":"
set passwd [lindex $argv 0]

spawn scp raspberrypi_rc_car.tar.gz kingbrady@caesar.elte.hu:../web
expect -re $prompt
send "$passwd\r"
sleep 1
expect eof