from unittest import TestCase
from unittest.mock import MagicMock
import controllers.gpio.distance_sensor


controllers.gpio.distance_sensor.setup = MagicMock()
controllers.gpio.distance_sensor.output = MagicMock()
controllers.gpio.distance_sensor.sleep = MagicMock()


class TestDistanceSensor(TestCase):

    ECHO = 1
    TRIGGER = 2

    def setUp(self) -> None:
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
        controllers.gpio.distance_sensor.gpio_input = MagicMock(side_effect=[0, 1, 1, 0])
        self.assertTrue(0 < self.distance_sensor.distance < 200)
        self.distance_sensor.logger.warning.assert_not_called()
        controllers.gpio.distance_sensor.gpio_input = MagicMock(side_effect=[
            0 if i < 100 or i > 200 else 1 for i in range(300)
        ])
        self.assertTrue(0 < self.distance_sensor.distance < 200)
        self.distance_sensor.logger.warning.assert_not_called()
