from json import dumps, loads
from random import randint
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, error as socket_error
from subprocess import run, check_output
from sys import maxsize
from threading import Thread
from time import sleep

from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE, advertise_service
from requests import get, post

from controller import Controller


GOOGLE_DOMAIN = 'https://google.com/'
CAESAR_URL = 'https://kingbrady.web.elte.hu/rc_car/{}.php'
GOOGLE_PUBLIC_DNS = '8.8.8.8'
ADDR_ANY = ''

COMMAND_GET_NETWORK_ADDRESS = ['sudo', 'iwgetid']
COMMAND_TURN_BLUETOOTH_DISCOVERY_ON = 'sh/bt_disc_on'
COMMAND_POWEROFF = 'sudo poweroff'

NETWORK_TIMEOUT_TOLERANCE = 1
RECV_MAX_BYTES = 1024

UUID = '94f39d29-7d6d-583a-973b-fba39e49d4ee'
BT_NAME = 'RC_car_raspberrypi'

PASSWORD_FILE = 'passwd'
POWEROFF = 'POWEROFF'


class RcCar:

    def __init__(self):
        self.controller = Controller()
        self.power_on = True
        self.is_connection_alive = False
        self.db_id = 1  # TODO: from file (file created during init)

        self.is_lan_active = self.__setup_lan_connection()
        self.is_bt_active = self.__setup_bt_connection()

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

    def __setup_lan_connection(self) -> bool:
        try:
            get(GOOGLE_DOMAIN, timeout=NETWORK_TIMEOUT_TOLERANCE)
        except Exception as e:
            # TODO: handle no internet (bluetooth, red LED)
            print(f'Exception happened during get request:\n{e}')
            return False

        self.lan_socket = socket(AF_INET, SOCK_STREAM)
        self.lan_socket.bind((ADDR_ANY, PORT_ANY))
        # although PORT_ANY is imported from bluetooth lib, its value is 0, and have the same symbolic meaning in both
        # bluetooth, and python socket libraries. Since such constant is not provided by the socket library it is
        # reasonable to use it here as well

        post(CAESAR_URL.format('update'), params={
            'id': self.db_id,
            'ip': RcCar.__get_ip(),
            'port': self.lan_socket.getsockname()[1],
            'ssid': RcCar.__get_ssid(),
            'available': 1
        })
        print(f'LAN port: {self.lan_socket.getsockname()[1]}, ssid: {RcCar.__get_ssid()}, ip: {self.lan_socket.getsockname()[0]}')

        self.lan_socket.listen()
        self.lan_socket.settimeout(1)
        return True

    def __setup_bt_connection(self) -> bool:
        run(COMMAND_TURN_BLUETOOTH_DISCOVERY_ON, shell=True)
        self.bt_socket = BluetoothSocket(RFCOMM)
        self.bt_socket.bind((ADDR_ANY, PORT_ANY))
        self.bt_socket.settimeout(1)
        self.bt_socket.listen(maxsize)

        port = self.bt_socket.getsockname()[1]

        advertise_service(
            self.bt_socket,
            BT_NAME,
            service_id=UUID,
            service_classes=[UUID, SERIAL_PORT_CLASS],
            profiles=[SERIAL_PORT_PROFILE]
        )
        print(f'BT port: {port}, uuid: {UUID}')
        return True

    def __receive_connection(self, server_socket) -> None:
        connection_made = False
        timestamp_timer = 0
        print(f'Accepting {"LAN" if server_socket.getsockname()[0] == "0.0.0.0" else "BT"} Connection...')
        while not self.is_connection_alive:
            if timestamp_timer > 30 and server_socket.getsockname()[0] == '0.0.0.0':
                timestamp_timer = 0
                post(CAESAR_URL.format('activate'), params={'id': self.db_id})
            try:
                self.message_socket, _ = server_socket.accept()
                connection_made = True
                self.is_connection_alive = True
            except socket_error:
                timestamp_timer += 1

        if not connection_made:
            print(f'returning, since {"LAN" if server_socket.getsockname()[0] != "0.0.0.0" else "BT"} connected..')
            return

        # TODO: better hashing algorithm
        # self.password = pbkdf2_hmac('sha256', b'69420', b'1234', 1000, 64)
        with open(PASSWORD_FILE, 'rb') as f:
            self.password = f.readline()

        received_password = self.message_socket.recv(RECV_MAX_BYTES)
        print(f'pwd: {self.password}\nrec: {received_password}')
        if self.password == received_password:
            print('...GRANTED')
            self.message_socket.sendall('GRANTED\n'.encode())
            self.is_connection_alive = True
        else:
            print('...REJECTED')  # TODO: error handling

    def __close_sockets(self):
        try:
            print('closing connections')
            self.message_socket.close()
        except Exception:
            pass

    def run(self) -> None:

        while self.power_on:
            post(CAESAR_URL.format('activate'), params={'id': self.db_id})
            try:
                lan_thread = None
                bt_thread = None

                if self.is_lan_active:
                    lan_thread = Thread(target=self.__receive_connection, args=(self.lan_socket,))
                    lan_thread.start()

                if self.is_bt_active:
                    bt_thread = Thread(target=self.__receive_connection, args=(self.bt_socket,))
                    bt_thread.start()

                if lan_thread:
                    lan_thread.join()
                if bt_thread:
                    bt_thread.join()
                post(CAESAR_URL.format('deactivate'), params={'id': self.db_id})

                update_thread = Thread(target=self.send_updates)
                update_thread.start()
                self.receive_commands()
                update_thread.join()
            except Exception as e:
                print(e)
                self.is_connection_alive = False
            finally:
                self.__close_sockets()

        print('closing main socket before exiting..')
        try:
            self.lan_socket.close()
        except:
            pass

# next line turns off the system how it should, however for convenience reasons it is commented out during development
        # run(COMMAND_POWEROFF, shell=True)
        
    def receive_commands(self) -> None:

        while True:
            data = self.message_socket.recv(1024).decode()
            if not data:
                self.is_connection_alive = False
                break
            elif data == POWEROFF:
                print('POWEROFF request received')
                self.power_on = False
            else:
                self.controller.set_values(loads(data))

    def send_updates(self) -> None:

        while self.is_connection_alive:
            message = dumps(self.controller.get_values()) + '\n'
            self.message_socket.sendall(message.encode())
            sleep(0.05)  # distance sensor


if __name__ == '__main__':
    RcCar().run()
