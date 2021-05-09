from unittest.mock import MagicMock


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
