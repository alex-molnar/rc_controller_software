#!/bin/bash

PATH_TO_ROOT_DIR=/home/alex/rc_controller_software

files=(
  "controller.py"
  "rc_software.py"
  "sockets/socket_base.py"
  "sockets/lan_socket.py"
  "sockets/bt_socket.py"
  "controllers/motor.py"
  "controllers/lighting.py"
  "controllers/gpio/buzzer.py"
  "controllers/gpio/leds.py"
  "controllers/gpio/output_device.py"
  "controllers/gpio/servo.py"
  "controllers/gpio/gpio_setup_cleanup.py"
  "controllers/gpio/line_sensor.py"
  "controllers/gpio/wheel.py"
  "sh/bt_disc_on.sh"
)

exit_notify() {
  printf "%b\nStopping now.\n" "$1"
  exit
}

cd "$PATH_TO_ROOT_DIR" || exit_notify "Changing directory failed"
mkdir raspberrypi_rc_car
cd raspberrypi_rc_car || exit_notify "Changing directory failed"
mkdir controllers
mkdir sh
mkdir sockets
cd controllers || exit_notify "Changing directory failed"
mkdir gpio
cd ../..

for file in "${files[@]}"; do
  cp "src/$file" "raspberrypi_rc_car/$file"
done

cp "requirements.txt" "raspberrypi_rc_car/requirements.txt"

old_path=$( (echo "$PATH_TO_ROOT_DIR/src"|sed -r 's/([\$\.\*\/\[\\^])/\\\1/g'|sed 's/[]]/\[]]/g')>&1)
new_path=$( (echo '/opt/raspberrypi_rc_car'|sed -r 's/([\$\.\*\/\[\\^])/\\\1/g'|sed 's/[]]/\[]]/g')>&1)
sed -i -e "s/$old_path/$new_path/g" "$PATH_TO_ROOT_DIR/raspberrypi_rc_car/rc_software.py" || exit_notify "Editing path to config file failed."
sed -i -e "s/$old_path/$new_path/g" "$PATH_TO_ROOT_DIR/raspberrypi_rc_car/sockets/bt_socket.py" || exit_notify "Editing path to config file failed."
sed -i 's/\r$//' sh/installScript.sh

tar -czvf raspberrypi_rc_car.tar.gz raspberrypi_rc_car >/dev/null 2>&1 || exit_notify "Compressing directory failed"
password=$(cat < passwd)
sh/upload.sh "$password" raspberrypi_rc_car.tar.gz
sh/upload.sh "$password" sh/installScript.sh
rm -r raspberrypi_rc_car
rm raspberrypi_rc_car.tar.gz