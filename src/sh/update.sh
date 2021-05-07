#!/bin/bash

exit_notify() {
  setup_gpio "19"
  printf "%b\nThe installation failed!\nClearing up and exiting" "$1"
  sleep 0.4
  printf "."
  sleep 0.4
  printf "."
  sleep 0.2
  printf "Done.\n"
  exit
}

setup_gpio() {
  sudo echo "$1" > /sys/class/gpio/export
  sudo echo "out" > "/sys/class/gpio/gpio$1/direction"
  sudo echo "1" > "/sys/class/gpio/gpio$1/value"
}

teardown_gpio() {
  sudo echo "0" > "/sys/class/gpio/gpio$1/value"
  sudo echo "$1" > /sys/class/gpio/unexport
}

TRY_ROOT="Try to run the script with root permissions!"
DOWNLOAD_FILE=raspberrypi_rc_car.tar.gz
latest_version=$(curl --silent -X GET "https://kingbrady.web.elte.hu/rc_car/get_version.php")
installed_version=$(cat < /opt/raspberrypi_rc_car/VERSION.txt)

sleep 2
if [ "$latest_version" == "$installed_version" ]; then
  printf "Already up to date!\n"
else
  cd /home/pi || exit_notify "Changing directory failed. $TRY_ROOT"
  sudo mv /opt/raspberrypi_rc_car/config.json config.json
  printf "Old version found: %s\nLatest version: %s\n Killing Running processes.." "$installed_version" "$latest_version"

  setup_gpio "16"
  while read -r p; do
    stats=(${p//./ })
    if [ "${stats[5]}" == "/opt/raspberrypi_rc_car/rc_software" ] || [ "${stats[6]}" == "/opt/raspberrypi_rc_car/rc_software" ]; then
      sudo kill -SIGKILL "${stats[0]}"
    fi
  done < <(sudo ps a)
  printf 'Done.\nUpdating packages [          ]\n'

  curl "https://kingbrady.web.elte.hu/raspberrypi_rc_car-$latest_version.tar.gz" --silent --output $DOWNLOAD_FILE
  printf '\e[1A\e[KUpdating packages [###       ]\n'

  sudo rm -rf /opt/raspberrypi_rc_car >/dev/null 2>&1 || exit_notify "FAIL.\nRemoving old files failed. $TRY_ROOT"
  sudo tar xzf $DOWNLOAD_FILE -C /opt >/dev/null 2>&1 || exit_notify "FAIL.\nExtracting files failed. $TRY_ROOT"
  printf '\e[1A\e[KUpdating packages [######    ]\n'

  mv "/opt/raspberrypi_rc_car-$latest_version" /opt/raspberrypi_rc_car
  rm -f $DOWNLOAD_FILE
  sudo mv config.json /opt/raspberrypi_rc_car/config.json
  cd /opt/raspberrypi_rc_car || exit_notify "Changing directory failed $TRY_ROOT"
  sudo chmod +x sh/update.sh
  sudo sed -i 's/\r$//' sh/update.sh
  printf "%s" "$latest_version" > VERSION.txt
  printf '\e[1A\e[KUpdating packages [##########] Done.\nUpdating python packages [          ]\n'

  python3 -m venv venv
  printf '\e[1A\e[KUpdating python packages [##        ]\n'

  venv/bin/pip install --upgrade pip >/dev/null 2>&1 || exit_notify "Installing python packages failed. $TRY_ROOT"
  printf '\e[1A\e[KUpdating python packages [#####     ]\n'

  venv/bin/pip install -r requirements.txt >/dev/null 2>&1 || exit_notify "Installing python packages failed. $TRY_ROOT"
  printf '\e[1A\e[KUpdating python packages [########  ]\n'

  venv/bin/pip install "rc_packages-$latest_version.tar.gz" >/dev/null 2>&1 || exit_notify "Installing python packages failed. $TRY_ROOT"
  printf "\e[1A\e[KUpdating python packages [##########] Done.\nTurning off now..\n"

  teardown_gpio "16"
  sudo poweroff
fi
