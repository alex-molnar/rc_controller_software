#!/bin/bash

files=(
  "controller.py"
  "rc_software.py"
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

cd ..
mkdir raspberrypi_rc_car
cd raspberrypi_rc_car || exit_notify "Changing directory failed"
mkdir controllers
mkdir sh
cd controllers || exit_notify "Changing directory failed"
mkdir gpio
cd ../..

for file in "${files[@]}"; do
  cp "src/$file" "raspberrypi_rc_car/$file"
done

tar -czvf raspberrypi_rc_car.tar.gz raspberrypi_rc_car >/dev/null 2>&1 || exit_notify "Compressing directory failed"
password=$(cat < passwd)
sh/upload.sh "$password"
rm -r raspberrypi_rc_car
rm raspberrypi_rc_car.tar.gz