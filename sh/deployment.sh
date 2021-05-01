#!/bin/bash

PATH_TO_ROOT_DIR=/home/alex/rc_controller_software

files=(
  "controller.py"
  "rc_software.py"
  "sh/bt_disc_on.sh"
)

exit_notify() {
  printf "%b\nStopping now.\n" "$1"
  exit
}

printf "Coping files.."

cd "$PATH_TO_ROOT_DIR" || exit_notify "Changing directory failed"
mkdir raspberrypi_rc_car
cd raspberrypi_rc_car || exit_notify "Changing directory failed"
mkdir sh
cd ..

for file in "${files[@]}"; do
  cp "src/$file" "raspberrypi_rc_car/$file"
done

cp "requirements.txt" "raspberrypi_rc_car/requirements.txt"

printf "Done.\nParsing files.."
password=$(cat < passwd)
[ -f VERSION.txt ] && old_version=$(cat < VERSION.txt) || old_version="1.0.0"
version_types=(${old_version//./ })
major=${version_types[0]}
minor=${version_types[1]}
continuous=${version_types[2]}

case "$1" in
  "-ma" | "--major")
    major=$(($major + 1))
    minor=0
    continuous=0
    ;;
  "-mi" | "--minor")
    minor=$(($minor + 1))
    continuous=0
    ;;
  *) continuous=$(($continuous + 1));;
esac

version="$major.$minor.$continuous"
printf "%s" "$version"  > VERSION.txt
curl --silent -X POST -F "version=$version" https://kingbrady.web.elte.hu/rc_car/set_version.php

printf "Done.\nCreating packages [#         ]\n"

old_path=$( (echo "$PATH_TO_ROOT_DIR/src"|sed -r 's/([\$\.\*\/\[\\^])/\\\1/g'|sed 's/[]]/\[]]/g')>&1)
new_path=$( (echo '/opt/raspberrypi_rc_car'|sed -r 's/([\$\.\*\/\[\\^])/\\\1/g'|sed 's/[]]/\[]]/g')>&1)
sed -i -e "s/$old_path/$new_path/g" "$PATH_TO_ROOT_DIR/raspberrypi_rc_car/rc_software.py" || exit_notify "Editing path to config file failed."
sed -i -e "s/$old_path/$new_path/g" "$PATH_TO_ROOT_DIR/src/sockets/bt_socket.py" || exit_notify "Editing path to config file failed."
sed -i -e "s/VERSION=0/VERSION='$version'/g" sh/installScript.sh
sed -i 's/\r$//' sh/installScript.sh
sed -i 's/\r$//' sh/chpasswd.sh

tar czf raspberrypi_rc_car.tar.gz raspberrypi_rc_car >/dev/null 2>&1 || exit_notify "Compressing directory failed"

printf "\e[1A\e[KCreating packages [#####     ]\n"

python3 -m build >/dev/null 2>&1

printf "\e[1A\e[KCreating packages [##########] Done.\n"

cd dist || exit_notify "Changing directory failed"
tar xzf "raspberrypi_rc_car_packages-$version.tar.gz"
echo -n "$version" > "raspberrypi_rc_car_packages-$version/VERSION.txt"
tar czf "raspberrypi_rc_car_packages-$version.tar.gz" "raspberrypi_rc_car_packages-$version"
cd ..

printf "Uploading files to server [#         ]\n"

sh/upload.sh "$password" "dist/raspberrypi_rc_car_packages-$version.tar.gz" >/dev/null 2>&1 || exit_notify "Uploading files failed"
printf '\e[1A\e[KUploading files to server [###       ]\n'
sh/upload.sh "$password" raspberrypi_rc_car.tar.gz >/dev/null 2>&1 || exit_notify "Uploading files failed"
printf '\e[1A\e[KUploading files to server [#####     ]\n'
sh/upload.sh "$password" sh/installScript.sh >/dev/null 2>&1 || exit_notify "Uploading files failed"
printf '\e[1A\e[KUploading files to server [########  ]\n'
sh/upload.sh "$password" sh/chpasswd.sh >/dev/null 2>&1 || exit_notify "Uploading files failed"
printf '\e[1AUploading files to server [##########] Done.\nCleaning up..'

rm -rf raspberrypi_rc_car
rm -f raspberrypi_rc_car.tar.gz
sed -i -e "s/$new_path/$old_path/g" "$PATH_TO_ROOT_DIR/src/sockets/bt_socket.py" || exit_notify "Editing path to config file failed."
rm -rf dist
rm -rf build
sh/execute.sh "$password" "rm ../web/raspberrypi_rc_car_packages-$old_version.tar.gz" >/dev/null 2>&1 || exit_notify "Removing old version from Caesar server failed"

printf "Done.\nDeployment finished.\n"