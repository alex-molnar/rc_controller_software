from json import dumps, loads
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, error as socket_error
from requests import get, post
from random import randint
from subprocess import run, check_output

from controller import Controller

from time import sleep


class RcCar:

    def __init__(self):
        self.controller = Controller()
        self.power_on = True
        self.is_connection_alive = False
        self.db_id = 1  # TODO: from file (file created during init)

        self.is_lan_active = self.__setup_lan_connection()
        self.is_bt_active = False  # bluetooth setup here

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
        print(f"port: {local_port}, ssid: {RcCar.__get_ssid()}")

        self.lan_socket.listen()
        self.lan_socket.settimeout(3)
        return True

    def __receive_lan_connection(self) -> None:
        lan_connection_made = False
        print("Accepting LAN Connection...")
        while not self.is_connection_alive:
            try:
                self.receiving_socket, _ = self.lan_socket.accept()
                self.sending_socket, _ = self.lan_socket.accept()
                lan_connection_made = True
                self.is_connection_alive = True
            except socket_error:
                pass

        if not lan_connection_made:
            print("returning, since bluetooth connected..")
            return

        # TODO: better hashing algorithm
        # self.password = pbkdf2_hmac('sha256', b'69420', b'1234', 1000, 64)
        with open('passwd', 'rb') as f:
            self.password = f.readline()

        received_password = self.receiving_socket.recv(1024)
        print(f'pwd: {self.password}\nrec: {received_password}')
        if self.password == received_password:
            print('...GRANTED')
            self.sending_socket.sendall('GRANTED\n'.encode())
            self.is_connection_alive = True
        else:
            print('...REJECTED')  # TODO: error handling

    def __receive_bt_connection(self) -> None:
        raise NotImplementedError

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

        while self.power_on:
            post("https://kingbrady.web.elte.hu/rc_car/activate.php", params={"id": self.db_id})
            try:
                lan_thread = None
                bt_thread = None

                if self.is_lan_active:
                    lan_thread = Thread(target=self.__receive_lan_connection)
                    lan_thread.start()

                if self.is_bt_active:
                    bt_thread = Thread(target=self.__receive_bt_connection)
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
            data = self.receiving_socket.recv(1024).decode()
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
            self.sending_socket.sendall(message.encode())
            try:
                _ = self.sending_socket.recv(1024)
            except:
                pass  # There is a chance the socket closes on the other side before this call gets made
            sleep(0.05)  # distance sensor


if __name__ == '__main__':
    RcCar().run()
