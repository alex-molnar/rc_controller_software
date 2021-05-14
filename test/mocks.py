from unittest.mock import MagicMock
from queue import Empty


class PWMMock:
    def __init__(self):
        self.ChangeDutyCycle = MagicMock()
        self.start = MagicMock()

    def stop(self):
        pass


class GeneralPurposeOutputDeviceMock:
    def __init__(self, _=None, __=None, ___=None):
        self.on = MagicMock()
        self.off = MagicMock()
        self.super_called = True
        self._value = MagicMock()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val


class LEDMock(GeneralPurposeOutputDeviceMock):
    def __init__(self, _=None, __=None, ___=None):
        super().__init__()
        self.blink = MagicMock()


class SocketMock:
    def __init__(self, _=None, __=None):
        self.super_called = True

    def bind(self, _):
        pass

    def listen(self, _=None):
        pass

    def settimeout(self, _):
        pass

    def close(self):
        pass

    def recv(self, _):
        return b'password'


class MotorMock:
    def __init__(self, _=None, __=None):
        self.initialized = True
        self.left = MagicMock()
        self.right = MagicMock()
        self.forward = MagicMock()
        self.backward = MagicMock()
        self.stop = MagicMock()


class QueueMock:
    def __init__(self):
        self.initialized = True
        self.put = MagicMock()
        self.get_nowait = MagicMock(side_effect=Empty)
