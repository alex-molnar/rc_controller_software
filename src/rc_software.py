import controllers.gpio.gpio_setup_cleanup

from os import chdir, listdir, remove
from pathlib import Path

from json import dumps, loads, load, dump, JSONDecodeError
from subprocess import run, check_output
from time import sleep
from datetime import datetime
from threading import Thread
from requests import get, post
from requests.exceptions import RequestException
from collections import defaultdict
from typing import List, Tuple, Optional
from multiprocessing import Queue
from queue import Empty
from socket import socket, AF_INET, SOCK_DGRAM
import logging

from sockets.socket_base import SocketBase
from sockets.lan_socket import LANSocket
from sockets.bt_socket import BTSocket

from controller import Controller
from controllers.gpio.leds import StatusLED


RUN_DIRECTORY = '/home/alex/rc_controller_software/src'

CAESAR_URL = 'https://kingbrady.web.elte.hu/rc_car/{}.php'
GOOGLE_PUBLIC_DNS = '8.8.8.8'

COMMAND_GET_NETWORK_ADDRESS = ['sudo', 'iwgetid']
COMMAND_POWEROFF = 'sudo poweroff'
COMMAND_UPDATE = 'sudo sh/update.sh &'

NETWORK_TIMEOUT_TOLERANCE = 1

CONFIG_FILE = 'config.json'
POWEROFF_MESSAGE = 'POWEROFF'
DEFAULT = 'default'
MODIFY_REQUEST = 'modify'
UPDATE_REQUEST = 'update'
OLD_VERSION = 'old_version'
LATEST_VERSION = 'latest_version'


class RcCar:

    def __init__(self):
        chdir(RUN_DIRECTORY)
        Path('log').mkdir(exist_ok=True)
        log_files = sorted(listdir('log'))
        if len(log_files) == 10:
            remove(f'log/{log_files[0]}')

        self.logger = logging.getLogger('rc_controller')
        self.logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(f'log/{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        fh.setLevel(logging.DEBUG)

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)

        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)7s: %(message)s', '%Y-%m-%d %H:%M:%S'))
        sh.setFormatter(logging.Formatter('%(levelname)5s: %(message)s'))

        self.logger.addHandler(fh)
        self.logger.addHandler(sh)

        self.controller = Controller()
        self.power_on = True
        self.is_connection_alive = False

        self.status_led = StatusLED(19, 16)
        self.modify_request = None

        with open(CONFIG_FILE, 'r') as f:
            config = load(f)
            self.password = config['passwd']
            self.db_id = config['id']
            self.db_name = config['device_name']

        sockets = [LANSocket(), BTSocket()]
        for sock in sockets:
            sock.setup_connections()
        self.sockets: List[SocketBase] = list(filter(lambda s: s.is_active, sockets))

        try:
            post(CAESAR_URL.format('update'), data={
                'id': self.db_id,
                'name': self.db_name,
                'ip': RcCar.__get_ip(),
                'port': sockets[0].sock.getsockname()[1],
                'ssid': RcCar.__get_ssid(),
                'available': 1
            }, timeout=NETWORK_TIMEOUT_TOLERANCE)
        except RequestException:
            self.logger.warning('Caesar Server unavailable, could not set ip and port')
        except IndexError:
            self.logger.warning('The initialization of the LAN socket was unsuccessful, could not set ip, port')

        if len(self.sockets) == 0:
            self.color = StatusLED.RED
            self.logger.error('There is no instance of any socket available returning now')
        elif len(self.sockets) == len(sockets):
            self.color = StatusLED.PINK
        else:
            self.color = StatusLED.CYAN
        self.status_led.color = self.color

        self.message_queue = Queue()
        self.message_socket: SocketBase
        self.message_socket = None
        self.update = False
        self.old_version, self.latest_version = self.check_for_updates()

    @staticmethod
    def __get_ip() -> str:
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect((GOOGLE_PUBLIC_DNS, 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    @staticmethod
    def __get_ssid() -> str:
        return check_output(COMMAND_GET_NETWORK_ADDRESS).split(b'"')[1].decode()

    def check_for_updates(self) -> Tuple[Optional[str], Optional[str]]:
        try:
            with open('VERSION.txt', 'r') as f:
                old_version = f.readline().strip()
                latest_version = get(CAESAR_URL.format("get_version"))
                self.logger.info(f'Found version: {old_version} Latest available: {latest_version.content.decode()}')
                return old_version, latest_version.content.decode()
        except RequestException:
            self.logger.warning("Caesar server can't be reached. Could not look for updates.")
        return None, None

    def __activate(self) -> None:
        try:
            post(CAESAR_URL.format('activate'), data={'id': self.db_id}, timeout=NETWORK_TIMEOUT_TOLERANCE)
        except RequestException:
            self.logger.warning("Caesar server is unreachable, could not activate car in db")

    def __deactivate(self) -> None:
        try:
            post(CAESAR_URL.format('deactivate'), data={'id': self.db_id}, timeout=NETWORK_TIMEOUT_TOLERANCE)
        except RequestException:
            self.logger.warning("Caesar server is unreachable, could not deactivate car in db")

    def __run_session(self) -> None:
        self.__deactivate()
        self.status_led.color = StatusLED.ORANGE
        self.is_connection_alive = True

        update_thread = Thread(target=self.send_updates)
        update_thread.start()
        self.receive_commands()

        update_thread.join()
        self.status_led.color = self.color

    def finish(self) -> None:
        self.logger.debug('Closing main sockets before exiting')
        self.controller.line_sensor.finish()
        for sock in self.sockets:
            sock.close()

    # next line turns off the system how it should, however for convenience reasons it is commented out during development
    #     run(COMMAND_UPDATE if self.update else COMMAND_POWEROFF, shell=True)

    def set_message_socket(self) -> bool:
        success = False

        for sock in self.sockets:
            sock.cancel()
            message_socket = sock.get_message_socket()
            if message_socket is not None:
                self.message_socket = message_socket
                success = self.message_socket.authenticate(self.password)
        return success

    def __modify_config(self, data: dict) -> None:
        default_data = defaultdict(lambda: DEFAULT, data)
        if default_data['name'] == DEFAULT:
            default_data['name'] = self.db_name
        if default_data['new_password'] == DEFAULT:
            default_data['new_password'] = self.password

        config = {
            'id': self.db_id,
            'passwd': default_data['new_password'],
            'device_name': default_data['name'],
        }

        if default_data['old_password'] == self.password:
            self.logger.info("Config modified successfully")
            self.modify_request = True
            with open('config.json', 'w') as f:
                dump(config, f)
        else:
            self.logger.info("Config modification failed. Wrong password was provided.")
            self.modify_request = False

    def run(self) -> None:
        while self.power_on:
            self.__activate()
            try:
                threads = [Thread(target=sock.accept_connection, args=(self.message_queue,)) for sock in self.sockets]

                for thread in threads:
                    thread.start()

                self.message_queue.get(timeout=300)

                if self.set_message_socket():
                    self.power_on = True
                    self.__run_session()
            except Empty:
                self.power_on = False
                self.is_connection_alive = False
                for sock in self.sockets:
                    sock.cancel()
                self.logger.error('No connection has been made for 5 minutes. turning off for power saving reasons.')
            except Exception as e:
                self.logger.warning(f'Exception happened during execution: {e}')
                self.is_connection_alive = False
            finally:
                self.logger.debug('Closing connections')
                if self.message_socket is not None:
                    self.message_socket.close()

        self.finish()

    def receive_commands(self) -> None:

        while True:
            data = self.message_socket.recv().decode()
            if not data:
                self.is_connection_alive = False
                break
            elif data == POWEROFF_MESSAGE or data == UPDATE_REQUEST:
                self.logger.info(f'{data} request received')
                self.power_on = False
                self.update = data == UPDATE_REQUEST
            else:
                try:
                    loaded_data = loads(data)
                    if MODIFY_REQUEST in loaded_data.keys():
                        self.__modify_config(loaded_data)
                    else:
                        self.controller.set_values(loaded_data)
                except JSONDecodeError:
                    self.logger.debug('JSON decode error happened. Message lost')

    def send_updates(self) -> None:
        message = dumps({OLD_VERSION: self.old_version, LATEST_VERSION: self.latest_version}) + '\n'
        self.message_socket.sendall(message.encode())

        while self.is_connection_alive:
            data = self.controller.get_values()
            if self.modify_request is not None:
                data[MODIFY_REQUEST] = self.modify_request
                self.modify_request = None
            message = dumps(data) + '\n'
            self.message_socket.sendall(message.encode())
            sleep(0.05)


if __name__ == '__main__':
    RcCar().run()
