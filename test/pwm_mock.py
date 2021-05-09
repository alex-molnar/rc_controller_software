from unittest.mock import MagicMock


class PWMMock:
    def __init__(self):
        self.ChangeDutyCycle = MagicMock()
        self.start = MagicMock()

    def stop(self):
        pass
