from unittest import TestCase
from unittest.mock import MagicMock, patch

import controllers.gpio.wheel
from mocks import GeneralPurposeOutputDeviceMock


@patch('controllers.gpio.wheel.GeneralPurposeOutputDevice', return_value=GeneralPurposeOutputDeviceMock())
class TestWheel(TestCase):

    F_PIN = 1
    B_PIN = 2
    SPEED = 1

    def setup(self) -> None:
        self.wheel = controllers.gpio.wheel.Wheel(self.F_PIN, self.B_PIN)

    def test_setup(self, _):
        self.setup()
        self.assertTrue(self.wheel._forward_device.super_called)
        self.assertTrue(self.wheel._backward_device.super_called)

    def test_forward(self, _):
        self.setup()
        self.wheel.forward(self.SPEED)
        self.wheel._forward_device.on.assert_called_with(self.SPEED)
        self.wheel._backward_device.off.assert_called()

    def test_backward(self, _):
        self.setup()
        self.wheel.backward(self.SPEED)
        self.wheel._forward_device.off.assert_called()
        self.wheel._backward_device.on.assert_called_with(self.SPEED)

    def test_stop(self, _):
        self.setup()
        self.wheel.stop()
        self.wheel._forward_device.off.assert_called()
        self.wheel._backward_device.off.assert_called()
