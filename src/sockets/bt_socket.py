from typing import Optional
from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE, advertise_service, \
    BluetoothError
from logging import getLogger
from subprocess import run
from sys import maxsize
from multiprocessing import Queue

from sockets.socket_base import SocketBase, ADDR_ANY, PORT_ANY

COMMAND_TURN_BLUETOOTH_DISCOVERY_ON = '/home/alex/rc_controller_software/src/sh/bt_disc_on.sh >/dev/null 2>&1'
UUID = '94f39d29-7d6d-583a-973b-fba39e49d4ee'
BT_NAME = 'RC_car_raspberrypi'


class BTSocket(SocketBase):
    def __init__(self, sock: BluetoothSocket = None):
        super(BTSocket, self).__init__()
        self.name = 'Bluetooth'
        self.sock = sock
        self.message_socket: BluetoothSocket
        self.is_connection_alive = False

        self.logger = getLogger('rc_controller')

    def setup_connections(self) -> None:
        try:
            run(COMMAND_TURN_BLUETOOTH_DISCOVERY_ON, shell=True)
            self.sock = BluetoothSocket(RFCOMM)
            self.sock.bind((ADDR_ANY, PORT_ANY))
            self.sock.settimeout(1)
            self.sock.listen(maxsize)

            advertise_service(
                self.sock,
                BT_NAME,
                service_id=UUID,
                service_classes=[UUID, SERIAL_PORT_CLASS],
                profiles=[SERIAL_PORT_PROFILE]
            )
        except BluetoothError:
            self.is_active = False
            self.logger.warning('Bluetooth exception happened during setup')
        except Exception as e:
            self.is_active = False
            self.logger.warning(f'Some other exception happened during bluetooth setup: {e}')

        self.logger.info('Bluetooth connection has been set up successfully')
        self.is_active = True

    def accept_connection(self, message_queue: Queue) -> None:
        self.is_connection_alive = False
        self.message_socket = None
        while not self.is_connection_alive:
            try:
                self.message_socket, conn_data = self.sock.accept()
                self.is_connection_alive = True
                self.logger.info(f'Connection accepted from {conn_data} via {self.name} socket')
            except BluetoothError:
                pass

        if self.message_socket is None:
            self.logger.debug(f'Returning from accept {self.name} connection, since an other device connected')
        else:
            message_queue.put("finished")

    def get_message_socket(self) -> Optional[SocketBase]:
        if self.message_socket is not None:
            return BTSocket(sock=self.message_socket)
