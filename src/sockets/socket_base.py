from multiprocessing import Queue
from time import sleep
from logging import getLogger
from socket import error as socket_error
from bluetooth import BluetoothError


ADDR_ANY = ''
PORT_ANY = 0

RECV_MAX_BYTES = 1024

GRANTED = 'granted'
REJECTED = 'rejected'
FINAL_REJECTION = 'final_rejection'


class SocketBase:
    def __init__(self):
        self.sock = None
        self.name = ''
        self.is_active = False
        self.is_connection_alive = False

        self.logger = getLogger('rc_controller')

    def setup_connections(self) -> None:
        raise NotImplementedError

    def accept_connection(self, message_queue: Queue) -> None:
        raise NotImplementedError

    def get_message_socket(self):
        raise NotImplementedError

    def authenticate(self, passwd: str) -> bool:
        tries = 1
        received_password = self.sock.recv(RECV_MAX_BYTES).decode()
        while received_password != passwd and tries < 3:
            self.logger.info(f'Wrong password provided in {self.name}. Available tries: {3 - tries}')
            self.sock.sendall(f'{REJECTED}\n'.encode())
            tries += 1
            received_password = self.sock.recv(RECV_MAX_BYTES).decode()

        if passwd == received_password:
            self.logger.info(f'Authentication was successful in {self.name}')
            self.sock.sendall(f'{GRANTED}\n'.encode())
            return True
        else:
            self.logger.info(f'Authentication was unsuccessful in {self.name}. Got wrong password 3 times')
            self.sock.sendall(f'{FINAL_REJECTION}\n'.encode())
            sleep(0.5)
            try:
                self.sock.close()
            except (BluetoothError, socket_error):
                pass
            return False

    def cancel(self) -> None:
        self.is_connection_alive = True

    def sendall(self, message: bytes) -> None:
        self.sock.sendall(message)

    def recv(self) -> bytes:
        return self.sock.recv(RECV_MAX_BYTES)

    def close(self) -> None:
        try:
            self.sock.close()
        except (BluetoothError, socket_error):
            pass
