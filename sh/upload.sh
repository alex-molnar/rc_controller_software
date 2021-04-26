#!/usr/bin/expect -f


set prompt ":"
set passwd [lindex $argv 0]
set file [lindex $argv 1]

spawn scp $file kingbrady@caesar.elte.hu:../web
expect -re $prompt
send "$passwd\r"
sleep 1
expect eof