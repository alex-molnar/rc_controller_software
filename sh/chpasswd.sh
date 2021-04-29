#!/usr/bin/expect -f


set prompt ":"
set passwd [lindex $argv 0]

spawn sudo passwd pi
expect -re $prompt
send "$passwd\r"
expect -re $prompt
send "$passwd\r"
sleep 1
expect eof