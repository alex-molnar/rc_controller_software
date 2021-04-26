import controllers.gpio.gpio_setup_cleanup

from os import chdir, listdir, remove
from pathlib import Path

from json import dumps, loads, load, dump, JSONDecodeError
from subprocess import run, check_output
from time import sleep
from datetime import datetime
from threading import Thread
from requests import post
from requests.exceptions import Timeout
from collections import defaultdict
from typing import List
from multiprocessing import Queue
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

NETWORK_TIMEOUT_TOLERANCE = 1

CONFIG_FILE = 'config.json'
POWEROFF = 'POWEROFF'
DEFAULT = 'default'
MODIFY_REQUEST = 'modify'


class RcCar:

    def __init__(self):
        chdir(RUN_DIRECTORY)
        Path('log').mkdir(exist_ok=True)
        log_files = sorted(listdir('log'))
        if len(log_files) == 10:
            remove(log_files[0])

        self.logger = logging.getLogger('rc_controller')
        self.logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(f'log/{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        fh.setLevel(logging.DEBUG)

        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)

        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)5s: %(message)s', '%Y-%m-%d %H:%M:%S'))
        sh.setFormatter(logging.Formatter('%(levelname)5s: %(message)s'))

        self.logger.addHandler(fh)
        self.logger.addHandler(sh)

        self.controllers = Controller()
        self.power_on = True
        self.is_connection_alive = False

        self.status_led = StatusLED(19, 16)

        with open(CONFIG_FILE, 'r') as f:
            config = load(f)
            self.password = config['passwd']
            self.db_id = config['id']
            self.db_name = config['device_name']

        sockets = [LANSocket(), BTSocket()]
        for sock in sockets:
            sock.setup_connections()
        self.sockets: List[SocketBase] = list(filter(lambda s: s.is_active, sockets))
        self.color = StatusLED.PINK if len(sockets) == len(self.sockets) else StatusLED.CYAN
        self.status_led.color = self.color

        post(CAESAR_URL.format('update'), params={
            'id': self.db_id,
            'name': self.db_name,
            'ip': RcCar.__get_ip(),
            'port': self.sockets[0].sock.getsockname()[1],
            'ssid': RcCar.__get_ssid(),
            'available': 1
        }, timeout=NETWORK_TIMEOUT_TOLERANCE)

        self.message_queue = Queue()
        self.message_socket: SocketBase

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

    def __activate(self):
        try:
            post(CAESAR_URL.format('activate'), params={'id': self.db_id}, timeout=NETWORK_TIMEOUT_TOLERANCE)
        except Timeout:
            self.logger.warning("Caesar server is unreachable, could not activate car in db")

    def __deactivate(self):
        try:
            post(CAESAR_URL.format('deactivate'), params={'id': self.db_id}, timeout=NETWORK_TIMEOUT_TOLERANCE)
        except Timeout:
            self.logger.warning("Caesar server is unreachable, could not deactivate car in db")

    def __run_session(self):
        self.__deactivate()
        self.status_led.color = StatusLED.ORANGE
        self.is_connection_alive = True

        update_thread = Thread(target=self.send_updates)
        update_thread.start()
        self.receive_commands()

        update_thread.join()
        self.status_led.color = self.color

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
            message = dumps({MODIFY_REQUEST: True}) + '\n'
            with open('config.json', 'w') as f:
                dump(config, f)
        else:
            self.logger.info("Config modification failed. Wrong password was provided.")
            message = dumps({MODIFY_REQUEST: False}) + '\n'

        self.message_socket.sendall(message.encode())

    def run(self) -> None:

        while self.power_on:
            self.__activate()
            try:
                threads = [Thread(target=sock.accept_connection, args=(self.message_queue,)) for sock in self.sockets]

                for thread in threads:
                    thread.start()

                self.message_queue.get()

                success = False

                for sock in self.sockets:
                    sock.cancel()
                    message_socket = sock.get_message_socket()
                    if message_socket is not None:
                        self.message_socket = message_socket
                        success = self.message_socket.authenticate(self.password)

                for thread in threads:
                    thread.join()

                if success:
                    self.__run_session()
            except Exception as e:
                self.logger.warning(f'Exception happened during execution: {e}')
                self.is_connection_alive = False
            finally:
                self.logger.debug('Closing connections')
                self.message_socket.close()

        self.logger.debug('Closing main sockets before exiting')
        self.controllers.line_sensor.finish()
        for sock in self.sockets:
            sock.close()

# next line turns off the system how it should, however for convenience reasons it is commented out during development
        # run(COMMAND_POWEROFF, shell=True)

    def receive_commands(self) -> None:

        while True:
            data = self.message_socket.recv().decode()
            if not data:
                self.is_connection_alive = False
                break
            elif data == POWEROFF:
                self.logger.info('POWEROFF request received')
                self.power_on = False
            else:
                try:
                    loaded_data = loads(data)
                    if MODIFY_REQUEST in loaded_data.keys():
                        self.__modify_config(loaded_data)
                    else:
                        self.controllers.set_values(loaded_data)
                except JSONDecodeError:
                    self.logger.debug('JSON decode error happened. Message lost')

    def send_updates(self) -> None:

        while self.is_connection_alive:
            message = dumps(self.controllers.get_values()) + '\n'
            self.message_socket.sendall(message.encode())
            sleep(0.05)


if __name__ == '__main__':
    RcCar().run()
