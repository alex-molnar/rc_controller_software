from unittest import TestCase
from unittest.mock import MagicMock, patch
from bluetooth import BluetoothError

import sockets.bt_socket
from mocks import SocketMock


sockets.bt_socket.BTSocket.__bases__ = (SocketMock,)
sockets.bt_socket.run = MagicMock()


@patch('sockets.bt_socket.BluetoothSocket', return_value=SocketMock())
class TestBTSocket(TestCase):

    def setup(self, sock=None):
        self.sock = sockets.bt_socket.BTSocket(sock)
        self.sock.logger.debug = MagicMock()
        self.sock.logger.info = MagicMock()
        self.sock.logger.warning = MagicMock()
        self.sock.logger.error = MagicMock()

    def test_setup(self, _):
        self.setup(SocketMock())
        self.assertTrue(self.sock.super_called)
        self.assertEqual('Bluetooth', self.sock.name)
        self.assertFalse(self.sock.is_connection_alive)
        self.assertTrue(self.sock.sock.super_called)

    def test_bluetooth_error(self, _):
        self.setup()
        sockets.bt_socket.advertise_service = MagicMock(side_effect=BluetoothError)
        self.sock.setup_connections()
        self.assertFalse(self.sock.is_active)

    def test_other_error(self, _):
        self.setup()
        sockets.bt_socket.advertise_service = MagicMock(side_effect=Exception)
        self.sock.setup_connections()
        self.assertFalse(self.sock.is_active)

    def test_should_be_active(self, _):
        self.setup()
        sockets.bt_socket.advertise_service = MagicMock()
        self.sock.setup_connections()
        self.assertTrue(self.sock.is_active)

    def test_get_socket(self, _):
        self.setup()
        self.sock.message_socket = SocketMock()
        ret = self.sock.get_message_socket()
        self.assertIsNotNone(ret)
        self.assertIsInstance(ret, sockets.bt_socket.BTSocket)

    def test_get_socket_none(self, _):
        self.setup()
        self.sock.message_socket = None
        self.assertIsNone(self.sock.get_message_socket())
