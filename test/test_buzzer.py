from unittest import TestCase
from unittest.mock import MagicMock

from mocks import GeneralPurposeOutputDeviceMock
import controllers.gpio.buzzer


controllers.gpio.buzzer.Buzzer.__bases__ = (GeneralPurposeOutputDeviceMock,)
controllers.gpio.buzzer.sleep = MagicMock()


class TestBuzzer(TestCase):

    PIN = 1
    BUZZ_VALUE = 5

    def setUp(self) -> None:
        self.buzzer = controllers.gpio.buzzer.Buzzer(self.PIN)

    def test_setup(self):
        self.assertTrue(self.buzzer.super_called)

    def test_sanity_checks(self):
        self.assertRaises(AssertionError, self.buzzer.buzz, 0)
        self.assertRaises(AssertionError, self.buzzer.buzz, -1)

    def test_buzz(self):
        self.buzzer.buzz(self.BUZZ_VALUE)
        self.buzzer.on.assert_called()
        self.buzzer.off.assert_called()
        controllers.gpio.buzzer.sleep.assert_called_with(self.BUZZ_VALUE)
