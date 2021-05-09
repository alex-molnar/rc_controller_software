from unittest import TestCase
from unittest.mock import MagicMock, patch
from requests.exceptions import Timeout
from socket import error as socket_error

import sockets.lan_socket
from mocks import SocketMock


sockets.lan_socket.LANSocket.__bases__ = (SocketMock,)
sockets.lan_socket.get = MagicMock()


@patch('sockets.lan_socket.socket', return_value=SocketMock())
class TestLANSocket(TestCase):

    def setup(self, db_id=None, sock=None):
        self.sock = sockets.lan_socket.LANSocket(db_id, sock)
        self.sock.logger.debug = MagicMock()
        self.sock.logger.info = MagicMock()
        self.sock.logger.warning = MagicMock()
        self.sock.logger.error = MagicMock()

    def test_setup(self, _):
        self.setup()
        self.assertTrue(self.sock.super_called)
        self.assertEqual('LAN', self.sock.name)
        self.assertFalse(self.sock.is_connection_alive)

    def test_initials(self, _):
        self.setup(10, SocketMock())
        self.assertEqual(10, self.sock.db_id)
        self.assertTrue(self.sock.sock.super_called)

    def test_no_internet(self, _):
        self.setup()
        sockets.lan_socket.get = MagicMock(side_effect=Timeout)
        self.sock.setup_connections()
        self.assertFalse(self.sock.is_active)
        sockets.lan_socket.get = MagicMock()

    def test_caesar_unreachable(self, _):
        self.setup()
        self.sock.logger.info = MagicMock(side_effect=Timeout)
        self.sock.setup_connections()
        self.assertFalse(self.sock.is_active)

    def test_socket_error(self, _):
        self.setup()
        self.sock.logger.info = MagicMock(side_effect=socket_error)
        self.sock.setup_connections()
        self.assertFalse(self.sock.is_active)

    def test_should_be_active(self, _):
        self.setup()
        self.sock.setup_connections()
        self.assertTrue(self.sock.is_active)

    def test_get_socket(self, _):
        self.setup()
        self.sock.message_socket = SocketMock()
        ret = self.sock.get_message_socket()
        self.assertIsNotNone(ret)
        self.assertIsInstance(ret, sockets.lan_socket.LANSocket)

    def test_get_socket_none(self, _):
        self.setup()
        self.sock.message_socket = None
        self.assertIsNone(self.sock.get_message_socket())
