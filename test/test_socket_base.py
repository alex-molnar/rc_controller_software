from unittest import TestCase
from unittest.mock import MagicMock

import sockets.lan_socket
from mocks import SocketMock
from sockets.socket_base import GRANTED, FINAL_REJECTION


sockets.lan_socket.LANSocket.__bases__ = (SocketMock,)
sockets.lan_socket.get = MagicMock()


class TestSocketBase(TestCase):

    def setUp(self):
        self.sock = sockets.lan_socket.SocketBase()
        self.sock.logger.debug = MagicMock()
        self.sock.logger.info = MagicMock()
        self.sock.logger.warning = MagicMock()
        self.sock.logger.error = MagicMock()

    def test_setup(self):
        self.assertEqual('', self.sock.name)
        self.assertIsNone(self.sock.sock)
        self.assertFalse(self.sock.is_active)
        self.assertFalse(self.sock.is_connection_alive)

    def test_authenticate_successful(self):
        self.sock.sock = SocketMock()
        self.sock.sock.sendall = MagicMock()
        self.sock.authenticate('password')
        self.sock.sock.sendall.assert_called_with(f'{GRANTED}\n'.encode())

    def test_authenticate_unsuccessful(self):
        self.sock.sock = SocketMock()
        self.sock.sock.sendall = MagicMock()
        self.sock.authenticate('wrong password')
        self.sock.sock.sendall.assert_called_with(f'{FINAL_REJECTION}\n'.encode())
