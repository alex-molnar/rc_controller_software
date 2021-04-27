#!/bin/bash

exit_notify() {
  printf "%b\nThe installation failed!\nClearing up and exiting" "$1"
  sleep 0.4
  printf "."
  sleep 0.4
  printf "."
  sleep 0.2
  printf "Done.\n"
  exit
}

log() {
  ! $silent && printf "%b" "$1"
}

DOWNLOAD_FILE=rc_car_curled.tar.gz
BLUETOOTH_NAME=RC_car_raspberrypi
TRY_ROOT="Try to run the script with root permissions!"

silent=false
default_inputs=false

for switch in "$@"; do
  case "$switch" in
    "-s" | "--silent") silent=true;;
    "-d" | "--default_inputs") default_inputs=true;;
  esac
done

# DOWNLOAD AND EXTRACT FILES
log "Downloading package.."
curl https://kingbrady.web.elte.hu/raspberrypi_rc_car.tar.gz --silent --output $DOWNLOAD_FILE

log "Done.\nExtracting package.."
tar -xzf $DOWNLOAD_FILE -C /opt >/dev/null 2>&1 || exit_notify "FAIL.\nExtracting files failed. $TRY_ROOT"
rm -f $DOWNLOAD_FILE
log "Done.\n"

cd /opt/raspberrypi_rc_car >/dev/null 2>&1 || exit_notify "Changing directory failed. $TRY_ROOT"

# SETTING UP CRONTAB
sudo echo "@reboot sudo python3 /opt/raspberrypi_rc_car/rc_software.py &" | sudo crontab - >/dev/null 2>&1 || exit_notify "Setting up the cronjob failed. $TRY_ROOT"

# INSTALLING PYTHON PACKAGES
sudo pip3 install --upgrade pip >/dev/null 2>&1 || exit_notify "Installing python packages failed. $TRY_ROOT"
sudo pip3 install -r requirements.txt >/dev/null 2>&1 || exit_notify "Installing python packages failed. $TRY_ROOT"

# SETTING UP BLUETOOTH
log "Setting up bluetooth.."
echo "system-alias '$BLUETOOTH_NAME'" | sudo bluetoothctl >/dev/null 2>&1 || exit_notify "Changing bluetooth name failed."
sudo sed -i -e 's/#DiscoverableTimeout = 0/DiscoverableTimeout = 0/g' /etc/bluetooth/main.conf || exit_notify "Editing bluetooth config file failed. $TRY_ROOT"
sudo systemctl daemon-reload >/dev/null 2>&1
sudo systemctl restart bluetooth.service >/dev/null 2>&1
sudo chmod +x sh/bt_disc_on.sh
sudo sh/bt_disc_on.sh >/dev/null 2>&1
log "Done.\n"

# SETTING UP CONFIG
printf "{\n" > config.json || exit_notify "Writing file config.json failed."

# WRITING NAME
if $default_inputs; then
  device_name="raspberrypi_rc_car$id"
  log "Default name was set to raspberrypi_rc_car$id\n"
else
  printf "Please provide a nice name for your car!\n"
  read -r device_name
fi

printf "  \"device_name\": \"%s\",\n" "$device_name" >> config.json
log "The device_name was set successfully.\n"

# REGISTERING TO DATABASE
key=$(echo -n $RANDOM | sha256sum | awk '{gsub(/[ -]+$/,""); print $0}')
log "Registering to database.."
curl --silent -X POST -F "name=$device_name" -F "key=${key%%*(-)}" https://kingbrady.web.elte.hu/rc_car/insert.php
log "Done.\n"

# WRITING ID
id=$(curl --silent -X GET "https://kingbrady.web.elte.hu/rc_car/get_id.php?key=$key")
printf "  \"id\": %s,\n" "$id" >> config.json
log "The id was set successfully.\n"

# WRITING PASSWORD
if $default_inputs; then
  passwd=0000
  log "Default password was set to 0000\n"
else
  printf 'Please enter a pin to be used when somebody connects to the car! [default: 0000]\nPassword: [0000]:'
  read -sr passwd
  [ -z "$passwd" ] && passwd=0000

  printf '\nPassword again:'
  read -sr passwd_clone
  [ -z "$passwd_clone" ] && passwd_clone=0000

  while [ "$passwd" != "$passwd_clone" ]; do
    printf '\nThe passwords did not match\nPassword: [0000]:'
    read -sr passwd
    printf '\nPassword again:'
    read -sr passwd_clone
  done
  printf "\n"
fi

printf "  \"passwd\": \"%s\"\n" "$(echo -n "$passwd" | sha256sum | awk '{gsub(/[ -]+$/,""); print $0}')" >> config.json
log "The password was set successfully.\n"

# FINISHING UP
printf "}\n" >> config.json
log "The installation finished successfully\n"
