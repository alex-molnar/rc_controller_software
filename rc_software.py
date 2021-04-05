from json import dumps, loads
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, error as socket_error
from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE, advertise_service, BluetoothError
from requests import get, post
from random import randint
from subprocess import run, check_output
from sys import maxsize

from controller import Controller

from time import sleep


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
        """
        Queries the IP address, which the socket is bind to.

        :Assumptions: None

        :return: The IPV4 address, which the socket is bind to
        """
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    @staticmethod
    def __get_ssid() -> str:
        return check_output(['sudo', 'iwgetid']).split(b'"')[1].decode()

    def __setup_lan_connection(self) -> bool:
        try:
            get("https://google.com/", timeout=3)
        except Exception as e:
            # TODO: handle no internet (bluetooth, red LED)
            print(f'Exception happened during get request:\n{e}')
            return False

        self.lan_socket = socket(AF_INET, SOCK_STREAM)
        listening = False

        while not listening:
            try:
                local_port = randint(15000, 60000)
                receiving_address = ('0.0.0.0', local_port)
                self.lan_socket.bind(receiving_address)
                listening = True
            except OSError as error:
                print(f"\r{error}", end='')

        post(
            "https://kingbrady.web.elte.hu/rc_car/update.php",
            params={
                "id": self.db_id,
                "ip": RcCar.__get_ip(),
                "port": local_port,
                "ssid": RcCar.__get_ssid(),
                "available": 1
            }
        )  # TODO: set timeout like 1 minute to invalidate port
        print(f"LAN port: {local_port}, ssid: {RcCar.__get_ssid()}")

        self.lan_socket.listen()
        self.lan_socket.settimeout(1)
        return True

    def __setup_bt_connection(self) -> bool:
        run('sh/bt_disc_on', shell=True)
        self.bt_socket = BluetoothSocket(RFCOMM)
        self.bt_socket.bind(("", PORT_ANY))
        self.bt_socket.settimeout(1)
        self.bt_socket.listen(maxsize)

        port = self.bt_socket.getsockname()[1]

        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

        advertise_service(
            self.bt_socket,
            "RC_car_raspberrypi",
            service_id=uuid,
            service_classes=[uuid, SERIAL_PORT_CLASS],
            profiles=[SERIAL_PORT_PROFILE]
        )
        print(f"BT port: {port}, uuid: {uuid}")
        return True

    def __receive_connection(self, server_socket) -> None:
        connection_made = False
        print(f"Accepting {'LAN' if server_socket.getsockname()[0] == '0.0.0.0' else 'BT'} Connection...")
        while not self.is_connection_alive:
            try:
                self.message_socket, _ = server_socket.accept()
                connection_made = True
                self.is_connection_alive = True
            except socket_error:
                pass

        if not connection_made:
            print(f"returning, since {'LAN' if server_socket.getsockname()[0] != '0.0.0.0' else 'BT'} connected..")
            return

        # TODO: better hashing algorithm
        # self.password = pbkdf2_hmac('sha256', b'69420', b'1234', 1000, 64)
        with open('passwd', 'rb') as f:
            self.password = f.readline()

        received_password = self.message_socket.recv(1024)
        print(f'pwd: {self.password}\nrec: {received_password}')
        if self.password == received_password:
            print('...GRANTED')
            self.message_socket.sendall('GRANTED\n'.encode())
            self.is_connection_alive = True
        else:
            print('...REJECTED')  # TODO: error handling

    def __close_sockets(self):
        try:
            print("closing connections")
            self.message_socket.close()
        except Exception:
            pass

    def run(self) -> None:

        while self.power_on:
            post("https://kingbrady.web.elte.hu/rc_car/activate.php", params={"id": self.db_id})
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
                post("https://kingbrady.web.elte.hu/rc_car/deactivate.php", params={"id": self.db_id})

                update_thread = Thread(target=self.send_updates)
                update_thread.start()
                self.receive_commands()
                update_thread.join()
            except Exception as e:
                print(e)
                self.is_connection_alive = False
            finally:
                self.__close_sockets()

        print("closing main socket before exiting..")
        try:
            self.lan_socket.close()
        except:
            pass

# next line turns off the system how it should, however for convenience reasons it is commented out during development
        # run("sudo poweroff", shell=True)
        
    def receive_commands(self) -> None:

        while True:
            data = self.message_socket.recv(1024).decode()
            if not data:
                self.is_connection_alive = False
                break
            elif data == "POWEROFF":
                print("POWEROFF request received")
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
