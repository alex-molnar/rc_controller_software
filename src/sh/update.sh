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

#cd raspberrypi_rc_car || exit_notify "Changing directory failed. $TRY_ROOT"
installed_version=$(cat < ../VERSION.txt)
latest_version=$(curl --silent -X GET "https://kingbrady.web.elte.hu/rc_car/get_version.php")
TRY_ROOT="Try to run the script with root permissions!"
DOWNLOAD_FILE=rc_car_curled.tar.gz
DOWNLOAD_FILE_PACKAGES=raspberrypi_rc_car_packages.tar.gz


if [ "$installed_version" == "$latest_version" ]; then
  printf "Already up to date!\n"
else
  cd /home/pi || exit_notify "Changing directory failed. $TRY_ROOT"
  printf "Old version found: %s\nLatest version: %s\nUpdating now [          ]\n" "$installed_version" "$latest_version"

  while read -r p; do
    stats=(${p//./ })
    if [ "${stats[5]}" == "/opt/raspberrypi_rc_car/rc_software" ] || [ "${stats[6]}" == "/opt/raspberrypi_rc_car/rc_software" ]; then
      sudo kill -SIGKILL "${stats[0]}"
    fi
  done < <(sudo ps a)
  printf '\e[1A\e[KUpdating now [#         ]\n'

  curl https://kingbrady.web.elte.hu/raspberrypi_rc_car.tar.gz --silent --output $DOWNLOAD_FILE
  printf '\e[1A\e[KUpdating now [###       ]\n'
  curl "https://kingbrady.web.elte.hu/raspberrypi_rc_car_packages-$latest_version.tar.gz" --silent --output $DOWNLOAD_FILE_PACKAGES
  printf '\e[1A\e[KUpdating now [#####     ]\n'

  sudo rm -rf /opt/raspberrypi_rc_car >/dev/null 2>&1 || exit_notify "FAIL.\nRemoving old files failed. $TRY_ROOT"
  printf '\e[1A\e[KUpdating now [######    ]\n'
  sudo tar xzf $DOWNLOAD_FILE -C /opt >/dev/null 2>&1 || exit_notify "FAIL.\nExtracting files failed. $TRY_ROOT"
  printf '\e[1A\e[KUpdating now [########  ]\n'
  sudo python3 -m pip install $DOWNLOAD_FILE_PACKAGES  >/dev/null 2>&1
  printf '\e[1A\e[KUpdating now [##########] Done.\nClearing up..'

  rm -f $DOWNLOAD_FILE
  rm -f $DOWNLOAD_FILE_PACKAGES
  printf "%s" "$latest_version" > /opt/raspberrypi_rc_car/VERSION.txt
  printf "Done.\n"
fi
