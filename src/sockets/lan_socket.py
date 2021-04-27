from requests import get, post, Timeout
from socket import socket, error as socket_error, AF_INET, SOCK_STREAM
from multiprocessing import Queue
from typing import Optional
from logging import getLogger

from sockets.socket_base import SocketBase, ADDR_ANY, PORT_ANY

GOOGLE_DOMAIN = 'https://google.com/'
CAESAR_URL = 'https://kingbrady.web.elte.hu/rc_car/{}.php'

NETWORK_TIMEOUT_TOLERANCE = 1


class LANSocket(SocketBase):
    def __init__(self, db_id: int = None, sock: socket = None):
        super(SocketBase, self).__init__()
        self.name = 'LAN'
        self.db_id = db_id
        self.sock = sock
        self.message_socket: socket
        self.is_connection_alive = False

        self.logger = getLogger('rc_controller')

    def setup_connections(self) -> None:
        try:
            get(GOOGLE_DOMAIN, timeout=NETWORK_TIMEOUT_TOLERANCE)
        except Timeout:
            self.logger.warning("There is no internet connection")
            self.is_active = False
            return

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.bind((ADDR_ANY, PORT_ANY))

            self.logger.info('LAN connection has been set up')
            self.sock.listen()
            self.sock.settimeout(1)
            self.is_active = True
        except socket_error as sock_err:
            self.logger.warning('A socket exception happened during LAN setup')
            self.logger.warning(sock_err)
            self.is_active = False
        except Timeout:
            self.logger.warning('Caesar server is unreachable')
            self.is_active = False

    def accept_connection(self, message_queue: Queue) -> None:
        timestamp_timer = 0
        self.is_connection_alive = False
        self.message_socket = None
        while not self.is_connection_alive:
            if timestamp_timer > 30:
                timestamp_timer = 0
                try:
                    post(CAESAR_URL.format('activate'), params={'id': self.db_id}, timeout=NETWORK_TIMEOUT_TOLERANCE)
                except Timeout:
                    self.logger.warning("Caesar server is unreachable, could not update timestamp")
            try:
                self.message_socket, conn_data = self.sock.accept()
                self.is_connection_alive = True
                self.logger.info(f'Connection accepted from {conn_data} via {self.name} socket')
            except socket_error:
                timestamp_timer += 1

        if self.message_socket is None:
            self.logger.debug(f'Returning from accept {self.name} connection, since an other device connected')
        else:
            message_queue.put("finished")

    def get_message_socket(self) -> Optional[SocketBase]:
        if self.message_socket is not None:
            return LANSocket(sock=self.message_socket)
