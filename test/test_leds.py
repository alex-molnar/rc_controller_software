from unittest import TestCase
from unittest.mock import MagicMock, patch

import controllers.gpio.leds
from mocks import GeneralPurposeOutputDeviceMock


controllers.gpio.leds.LED.__bases__ = (GeneralPurposeOutputDeviceMock,)
controllers.gpio.leds.Thread = MagicMock()
controllers.gpio.leds.sleep = MagicMock()


class TestLED(TestCase):

    PIN = 1

    def setUp(self) -> None:
        self.led = controllers.gpio.leds.LED(self.PIN)

    def test_setup(self):
        self.assertTrue(self.led.super_called)

    def test_blink_sanity_checks(self):
        self.assertRaises(AssertionError, self.led.blink, -2)
        self.assertRaises(AssertionError, self.led.blink, 0)
        self.assertRaises(AssertionError, self.led.blink, 1, -1)
        self.assertRaises(AssertionError, self.led.blink, 1, 0.3, -1)
        self.assertRaises(AssertionError, self.led.blink, 1, 0.3, 0.3, -1)
        self.assertRaises(AssertionError, self.led.blink, 1, 0.3, 0.3, 0.5, -1)

    def test_non_blocking_call(self):
        self.led.blink(5, non_blocking=True)
        controllers.gpio.leds.Thread.assert_called_with(target=self.led.blink, args=(5, 0.3, 0.3, 0.5, 0.5))


@patch('controllers.gpio.leds.LED', return_value=GeneralPurposeOutputDeviceMock())
class TestStatusLED(TestCase):

    RED_PIN = 1
    GREEN_PIN = 2
    COM_VAL = 150

    def setup(self, red_start_val=0, green_start_val=0):
        self.status_led = controllers.gpio.leds.StatusLED(self.RED_PIN, self.GREEN_PIN, red_start_val, green_start_val)

    def test_setup(self, _):
        self.setup()
        self.assertTrue(self.status_led.red_leg.super_called)
        self.assertTrue(self.status_led.green_leg.super_called)

    def test_initials(self, _):
        self.setup(self.COM_VAL, self.COM_VAL)
        self.assertEqual(self.COM_VAL / 255, self.status_led.red_leg.value)
        self.assertEqual(self.COM_VAL / 255, self.status_led.green_leg.value)
        # self.status_led.green_leg.value.assert_called_with(self.COM_VAL / 255)
        self.assertEqual((self.COM_VAL, self.COM_VAL, 255), self.status_led.color)

    def test_sanity_checks(self, _):
        self.setup()
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', None)
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', 'def not a valid tuple')
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', (0, 0))
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', (0, 0, 0, 0))
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', (300, 0, 0))
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', (0, 300, 0))
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', (-1, 0, 0))
        self.assertRaises(AssertionError, setattr, self.status_led, 'color', (0, -1, 0))
        self.status_led.color = (0, 0, 2352456245)
        self.status_led.color = (0, 0, -2352456245)
        # Either should raise AssertionError, since blue color does not matter, is connected to 3v3 directly,
        # can not be set programmatically

    def test_color(self, _):
        self.setup()
        self.status_led.color = (self.COM_VAL, 0, 0)
        self.assertEqual((self.COM_VAL, 0, 255), self.status_led.color)
        self.status_led.color = (0, self.COM_VAL, 0)
        self.assertEqual((0, self.COM_VAL, 255), self.status_led.color)
        self.status_led.color = (0, 0, self.COM_VAL)
        self.assertEqual((0, 0, 255), self.status_led.color)
