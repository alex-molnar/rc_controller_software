#!/bin/bash

PATH_TO_ROOT_DIR=/home/alex/rc_controller_software

files=(
  "controller.py"
  "rc_software.py"
  "sh/bt_disc_on.sh"
  "sh/update.sh"
)

exit_notify() {
  printf "%b\nStopping now.\n" "$1"
  exit
}

printf "Coping files.."

cd "$PATH_TO_ROOT_DIR" || exit_notify "Changing directory failed"

printf "Done.\nParsing files.."
password=$(cat < passwd)
[ -f VERSION.txt ] && old_version=$(cat < VERSION.txt) || old_version="1.0.0"
version_types=(${old_version//./ })
major=${version_types[0]}
minor=${version_types[1]}
micro=${version_types[2]}

case "$1" in
  "-ma" | "--major")
    major=$(($major + 1))
    minor=0
    micro=0
    ;;
  "-mi" | "--minor")
    minor=$(($minor + 1))
    micro=0
    ;;
  *) micro=$(($micro + 1));;
esac

version="$major.$minor.$micro"
printf "%s" "$version"  > VERSION.txt
curl --silent -X POST -F "version=$version" https://kingbrady.web.elte.hu/rc_car/set_version.php

mkdir "raspberrypi_rc_car-$version"
cd "raspberrypi_rc_car-$version" || exit_notify "Changing directory failed"
mkdir sh
cd ..

for file in "${files[@]}"; do
  cp "src/$file" "raspberrypi_rc_car-$version/$file"
done

venv/bin/pip freeze | grep -v "pkg-resources" > requirements.txt
# There is a bug in pip, when it gets wrong metadata from Debian-family OS-es, it puts pk-resources==0.0.0
# to the output of freeze, which then causes the installation to fail.
cp "requirements.txt" "raspberrypi_rc_car-$version/requirements.txt"

printf "Done.\nCreating packages.."

old_path=$( (echo "$PATH_TO_ROOT_DIR/src"|sed -r 's/([\$\.\*\/\[\\^])/\\\1/g'|sed 's/[]]/\[]]/g')>&1)
new_path=$( (echo '/opt/raspberrypi_rc_car'|sed -r 's/([\$\.\*\/\[\\^])/\\\1/g'|sed 's/[]]/\[]]/g')>&1)
sed -i -e "s/$old_path/$new_path/g" "$PATH_TO_ROOT_DIR/raspberrypi_rc_car-$version/rc_software.py" || exit_notify "Editing path to config file failed."
sed -i -e "s/$old_path/$new_path/g" "$PATH_TO_ROOT_DIR/src/sockets/bt_socket.py" || exit_notify "Editing path to config file failed."
sed -i -e "s/VERSION=0/VERSION='$version'/g" sh/installScript.sh
sed -i 's/\r$//' sh/installScript.sh
sed -i 's/\r$//' src/sh/update.sh

venv/bin/python3 -m build >/dev/null 2>&1

cd dist || exit_notify "Changing directory failed"
tar xzf "rc_packages-$version.tar.gz"
echo -n "$version" > "rc_packages-$version/VERSION.txt"
tar czf "rc_packages-$version.tar.gz" "rc_packages-$version"
cd ..
mv "dist/rc_packages-$version.tar.gz" "raspberrypi_rc_car-$version/rc_packages-$version.tar.gz"

tar czf "raspberrypi_rc_car-$version.tar.gz" "raspberrypi_rc_car-$version" >/dev/null 2>&1 || exit_notify "Compressing directory failed"

printf "Done.\nUploading files to server [#         ]\n"

sh/upload.sh "$password" "raspberrypi_rc_car-$version.tar.gz" >/dev/null 2>&1 || exit_notify "Uploading files failed"
printf '\e[1A\e[KUploading files to server [#####     ]\n'
sh/upload.sh "$password" sh/installScript.sh >/dev/null 2>&1 || exit_notify "Uploading files failed"
printf '\e[1AUploading files to server [##########] Done.\nCleaning up..'

rm -rf "raspberrypi_rc_car-$version"
rm -f "raspberrypi_rc_car-$version.tar.gz"
sed -i -e "s/$new_path/$old_path/g" "$PATH_TO_ROOT_DIR/src/sockets/bt_socket.py" || exit_notify "Editing path to config file failed."
rm -rf dist
rm -rf build
sh/execute.sh "$password" "rm ../web/raspberrypi_rc_car-$old_version.tar.gz" >/dev/null 2>&1 || exit_notify "Removing old version from Caesar server failed"

printf "Done.\nDeployment finished.\n"
