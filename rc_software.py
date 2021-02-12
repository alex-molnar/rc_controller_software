from json import dumps, loads
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from requests import get, post
from random import randint

from controller import Controller
from hashlib import sha256

from time import sleep


class RcCar:

    def __init__(self):
        try:
            get("https://google.com/", timeout=3)
        except Exception as e:
            # TODO: handle no internet (bluetooth, red LED)
            print(f'Exception happened during get request:\n{e}')

        conn = socket(AF_INET, SOCK_STREAM)
        listening = False

        while not listening:
            try:
                local_port = randint(15000, 60000)
                receiving_address = ('0.0.0.0', local_port)
                conn.bind(receiving_address)
                listening = True
            except OSError as error:
                print(f"\r{error}", end='')

        post("https://kingbrady.web.elte.hu/rc_car/update.php", params={"ip": RcCar.__get_ip(), "port": local_port})

        conn.listen()
        self.receiving_socket, _ = conn.accept()
        self.sending_socket, _ = conn.accept()
        conn.close()

        password = "69420"  # TODO: get password from file
        self.password = sha256(password.encode()).digest()

        received_password = self.receiving_socket.recv(1024)
        if password == received_password:
            print('...GRANTED')
            self.sending_socket.sendall('GRANTED\n'.encode())
            self.controller = Controller()
            self.is_connection_alive = True
        else:
            print('...REJECTED')

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

    def run(self) -> None:

        update_thread = Thread(target=self.send_updates)
        update_thread.start()
        self.receive_commands()
        update_thread.join()
        
    def receive_commands(self) -> None:

        while True:
            data = self.receiving_socket.recv(1024).decode()
            if not data:
                self.is_connection_alive = False
                break
            else:
                self.controller.set_values(loads(data))

    def send_updates(self) -> None:

        while self.is_connection_alive:
            message = dumps(self.controller.get_values()) + '\n'
            self.sending_socket.sendall(message.encode())
            _ = self.sending_socket.recv(1024)
            sleep(0.05)  # distance sensor


if __name__ == '__main__':
    RcCar().run()
