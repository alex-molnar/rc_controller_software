from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, timeout as SocketConnectionError
from random import randint
from time import sleep

from requests import post, get
from agent_base import AgentBase
from abc import ABCMeta
from multiprocessing import Queue
from utils.constants import SUCCESS, AUTHENTICATION_FAILURE, AGENT_CONNECTED


class LAN_AgentMeta(ABCMeta):
    def __str__(self):
        return 'LAN'


class LAN_Agent(AgentBase, metaclass=LAN_AgentMeta):
    """"""

    @staticmethod
    def poll(agent_queue: Queue) -> None:
        try:
            get("https://google.com/", timeout=3)
            lan_agent_instance = LAN_Agent()
            while lan_agent_instance.sending_socket is None or lan_agent_instance.receiving_socket is  None:
                lan_agent_instance = LAN_Agent()

            print("Creation of lan_agent was successful")
            agent_queue.put(lan_agent_instance)
            sleep(5)  # workaround: exiting this process closes the queue for some reason
        except Exception as e:
            # TODO: handle no internet (bluetooth)
            print(f'Exception happened during get request:\n{e}')

    def __init__(self):
        """""" 
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

        post("https://kingbrady.web.elte.hu/rc_car/update.php", params={"ip": self.__get_IP(), "port": local_port})

        conn.listen()
        conn.setblocking(True)

        try:
            self.receiving_socket, _ = conn.accept()
            self.sending_socket, _ = conn.accept()
        except SocketConnectionError:
            pass

        conn.close()

    def __str__(self):
        return 'LAN'

    def __get_IP(self) -> str:
        """
        Querys the IP address, which the socket is bind to.

        :Assumptions: None

        :return: The IPV4 address, which the socket is bind to
        """
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        IP = s.getsockname()[0]
        s.close()
        return IP

    def close_connection(self) -> None:
        try:
            self.sending_socket.close()
            self.receiving_socket.close()
        except:
            pass

    def authenticate(self, password: bytes) -> bool:
        received_password = self.receiving_socket.recv(1024)
        if password == received_password:
            print('...GRANTED')
            self.sending_socket.sendall('GRANTED\n'.encode())
            return True
        else:
            # Should probably send rejected message to handle wrong password (like 3 times then give back controll)
            print('...REJECTED')
            return False

    def receive(self) -> str:
        print('receiveing')
        mes = self.receiving_socket.recv(1024).decode()
        print(f'message received: {mes}')
        return mes

    def send(self, message: str) -> None:
        print(f'message sent: {message}')
        self.sending_socket.sendall(message.encode())
        _ = self.sending_socket.recv(1024)
