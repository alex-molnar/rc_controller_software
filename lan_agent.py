from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, timeout as SocketConnectionError
from random import randint
from requests import post, get
from agent_base import AgentBase
from utils.constants import SUCCESS, AUTHENTICATION_FAILURE, AGENT_CONNECTED


class LAN_Agent(AgentBase):
    """"""

    @staticmethod
    def get_instance(obj):
        try:
            get("https://google.com/", timeout=3)
            lan_agent_instance = LAN_Agent()
            if lan_agent_instance.sending_socket is not None and lan_agent_instance.receiving_socket is not None:
                print("Creation of lan_agent was successful")
                success = obj.set_agent(lan_agent_instance)
                if success == AUTHENTICATION_FAILURE:
                    print('Authentication failure')
                    lan_agent_instance.sending_socket.sendall(b"WRONG PASSWORD\n")
                    # TODO: handle asking for new password
                elif success == AGENT_CONNECTED:
                    print('agent already connected')
                    lan_agent_instance.close_connection()
        except Exception as e:
            # TODO: handle no internet (bluetooth)
            print(f'Exception happened during get request:\n{e}')
            raise e

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
        conn.settimeout(60)

        try:
            self.receiving_socket, _ = conn.accept()
            self.sending_socket, _ = conn.accept()
        except SocketConnectionError:
            pass

        conn.close()

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

    def receive_passwd(self) -> str:
        return self.receiving_socket.recv(1024)

    def send_passwd(self) -> None:
        print(f'message sending')
        self.sending_socket.sendall('GRANTED\n'.encode())
        print(f'message sent')

    def receive(self) -> str:
        print('receiveing')
        mes = self.receiving_socket.recv(1024).decode()
        print(f'message received: {mes}')
        return mes

    def send(self, message: str) -> None:
        print(f'message sent: {message}')
        self.sending_socket.sendall(message.encode())
        _ = self.sending_socket.recv(1024)
