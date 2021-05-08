from unittest import TestCase
from unittest.mock import MagicMock
import controllers.gpio.distance_sensor
from random import randint


controllers.gpio.distance_sensor.setup = MagicMock()
controllers.gpio.distance_sensor.output = MagicMock()
controllers.gpio.distance_sensor.sleep = MagicMock()


class TestDistanceSensor(TestCase):

    ECHO = 1
    TRIGGER = 2

    def setUp(self) -> None:
        self.val = 0
        self.distance_sensor = controllers.gpio.distance_sensor.DistanceSensor(echo=self.ECHO, trigger=self.TRIGGER)
        self.distance_sensor.logger.warning = MagicMock()

    def test_setups_happened_correctly(self):
        controllers.gpio.distance_sensor.setup.assert_called_with(self.TRIGGER, 0)
        controllers.gpio.distance_sensor.output.assert_called_with(self.TRIGGER, 1)

    def test_no_echo_to_low(self):
        controllers.gpio.distance_sensor.gpio_input = MagicMock(return_value=1)
        self.assertEqual(200.0, self.distance_sensor.distance)
        self.distance_sensor.logger.warning.assert_called()

    def test_no_echo_to_high(self):
        controllers.gpio.distance_sensor.gpio_input = MagicMock(return_value=0)
        self.assertEqual(200.0, self.distance_sensor.distance)
        self.distance_sensor.logger.warning.assert_called()

    def test_normal_value(self):
        controllers.gpio.distance_sensor.gpio_input = MagicMock(side_effect=lambda _: randint(0, 1))
        self.assertTrue(0 < self.distance_sensor.distance)
        self.assertTrue(200 > self.distance_sensor.distance)
        self.distance_sensor.logger.warning.assert_not_called()
