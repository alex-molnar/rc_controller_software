from json import dumps, loads
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM
from requests import get, post
from random import randint

from controller import Controller

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

        # TODO: delete values with some timeout
        post("https://kingbrady.web.elte.hu/rc_car/update.php", params={"ip": RcCar.__get_ip(), "port": local_port})  # TODO: set timeout like 1 minute to invalidate port
        print(f"port: {local_port}")

        conn.listen()
        self.receiving_socket, _ = conn.accept()
        self.sending_socket, _ = conn.accept()
        conn.close()

        # TODO: better hashing algorithm
        # self.password = pbkdf2_hmac('sha256', b'69420', b'1234', 1000, 64)
        with open('passwd', 'rb') as f:
            self.password = f.readline()

        received_password = self.receiving_socket.recv(1024)
        print(f'pwd: {self.password}\nrec: {received_password}')
        if self.password == received_password:
            print('...GRANTED')
            self.sending_socket.sendall('GRANTED\n'.encode())
            self.controller = Controller()
            self.is_connection_alive = True
        else:
            print('...REJECTED')  # TODO: error handling

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

    def __close_sockets(self):
        try:
            print("closing connections")
            self.sending_socket.close()
        except Exception:
            pass
        try:
            self.receiving_socket.close()
        except Exception:
            pass

    def run(self) -> None:

        try:
            update_thread = Thread(target=self.send_updates)
            update_thread.start()
            self.receive_commands()
            update_thread.join()
        except Exception as e:
            print(e)
        finally:
            self.__close_sockets()  # TODO: listen to connections again or something
        
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
            try:
                _ = self.sending_socket.recv(1024)
            except:
                pass  # There is a chance the socket closes on the other side before this call gets made
            sleep(0.05)  # distance sensor


if __name__ == '__main__':
    RcCar().run()
