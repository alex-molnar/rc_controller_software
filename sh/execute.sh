#!/usr/bin/expect -f


set prompt ":"
set passwd [lindex $argv 0]
set command [lindex $argv 1]

spawn ssh kingbrady@caesar.elte.hu "$command"
expect -re $prompt
send "$passwd\r"
sleep 1
expect eof