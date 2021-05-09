from unittest import TestCase
from unittest.mock import MagicMock, patch

import controllers.gpio.output_device
from pwm_mock import PWMMock


controllers.gpio.output_device.gpio_setup = MagicMock()


@patch('controllers.gpio.output_device.PWM', return_value=PWMMock())
class TestGeneralPurposeOutputDevice(TestCase):

    PIN = 1
    MIN_VAL = 0
    MAX_VAL = 1
    COM_VAL = 0.5

    def setup(self, start_val: float = MIN_VAL, max_val: float = MAX_VAL):
        self.output_device = controllers.gpio.output_device.GeneralPurposeOutputDevice(self.PIN, start_val, max_val)

    def test_setup(self, _):
        self.setup()
        controllers.gpio.output_device.gpio_setup.assert_called_with(self.PIN, 0)
        self.output_device._device.start.assert_called_with(self.MIN_VAL)
        self.assertFalse(self.output_device.is_active)

    def test_initials(self, _):
        self.setup(self.COM_VAL, 0.7)
        self.output_device._device.start.assert_called_with(50)
        self.assertEqual(self.COM_VAL, self.output_device.value)
        self.assertTrue(self.output_device.is_active)

    def test_setup_sanity_checks(self, _):
        self.assertRaises(AssertionError, self.setup, 0.5, 1.5)
        self.assertRaises(AssertionError, self.setup, 1, 0.7)
        self.assertRaises(AssertionError, self.setup, 0.5, -1)
        self.assertRaises(AssertionError, self.setup, -1, 1)

    def test_value_sanity_checks(self, _):
        self.setup()
        self.assertRaises(AssertionError, setattr, self.output_device, 'value', 2)
        self.assertRaises(AssertionError, setattr, self.output_device, 'value', -1)

    def test_on_sanity_checks(self, _):
        self.setup()
        self.assertRaises(AssertionError, self.output_device.on, 2)
        self.assertRaises(AssertionError, self.output_device.on, -1)

    def test_toggle_sanity_checks(self, _):
        self.setup()
        self.assertRaises(AssertionError, self.output_device.toggle, 2)
        self.assertRaises(AssertionError, self.output_device.toggle, -1)
        self.output_device.on()
        self.output_device.toggle(2)  # Should not raise AssertionError, since argument does not matter in this case
        self.output_device.on()
        self.output_device.toggle(-1)  # Should not raise AssertionError, since argument does not matter in this case

    def test_value_property(self, _):
        self.setup()
        self.assertFalse(self.output_device.is_active)
        self.output_device.value = self.COM_VAL
        self.assertTrue(self.output_device.is_active)
        self.assertEqual(self.COM_VAL, self.output_device.value)
        self.output_device._device.ChangeDutyCycle.assert_called_with(50)

    def test_on_without_argument(self, _):
        self.setup()
        self.assertFalse(self.output_device.is_active)
        self.output_device.on()
        self.assertTrue(self.output_device.is_active)
        self.assertEqual(self.MAX_VAL, self.output_device.value)
        self.output_device._device.ChangeDutyCycle.assert_called_with(100)

    def test_on_with_argument(self, _):
        self.setup()
        self.assertFalse(self.output_device.is_active)
        self.output_device.on(self.COM_VAL)
        self.assertTrue(self.output_device.is_active)
        self.assertEqual(self.COM_VAL, self.output_device.value)
        self.output_device._device.ChangeDutyCycle.assert_called_with(50)

    def test_off(self, _):
        self.setup(start_val=self.COM_VAL)
        self.assertTrue(self.output_device.is_active)
        self.output_device.off()
        self.assertFalse(self.output_device.is_active)
        self.assertEqual(self.MIN_VAL, self.output_device.value)
        self.output_device._device.ChangeDutyCycle.assert_called_with(0)

    def test_toggle_on_without_argument(self, _):
        self.setup()
        self.assertFalse(self.output_device.is_active)
        self.output_device.toggle()
        self.assertTrue(self.output_device.is_active)
        self.assertEqual(self.MAX_VAL, self.output_device.value)
        self.output_device._device.ChangeDutyCycle.assert_called_with(100)

    def test_toggle_on_with_argument(self, _):
        self.setup()
        self.assertFalse(self.output_device.is_active)
        self.output_device.toggle(self.COM_VAL)
        self.assertTrue(self.output_device.is_active)
        self.assertEqual(self.COM_VAL, self.output_device.value)
        self.output_device._device.ChangeDutyCycle.assert_called_with(50)

    def test_toggle_off(self, _):
        self.setup(start_val=self.COM_VAL)
        self.assertTrue(self.output_device.is_active)
        self.output_device.toggle()
        self.assertFalse(self.output_device.is_active)
        self.assertEqual(self.MIN_VAL, self.output_device.value)
        self.output_device._device.ChangeDutyCycle.assert_called_with(0)
