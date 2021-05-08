from unittest import TestCase
from unittest.mock import MagicMock
import controllers.gpio.line_sensor
from multiprocessing import Queue
from queue import Empty
from time import sleep

controllers.gpio.line_sensor.gpio_setup = MagicMock()


class TestLineSensor(TestCase):

    PIN = 1

    def setup(self, side_effect=[]) -> None:
        self.queue = Queue()
        controllers.gpio.line_sensor.gpio_input = MagicMock(side_effect=[*side_effect, *[0 for _ in range(100)]])
        self.on_line_sensor = controllers.gpio.line_sensor.LineSensor(self.PIN, self.on_line_change)
        sleep(0.1)

    def tearDown(self) -> None:
        self.on_line_sensor.finish()

    def on_line_change(self, val):
        self.queue.put(val)

    def test_setup(self):
        self.setup()
        controllers.gpio.line_sensor.gpio_setup.assert_called_with(self.PIN, 1)

    def test_on_line(self):
        self.setup([0, 1])
        self.assertFalse(self.queue.get_nowait())

    def test_on_no_line(self):
        self.setup([1])
        self.assertTrue(self.queue.get_nowait())

    def test_no_state_changed(self):
        self.setup()
        self.assertRaises(Empty, self.queue.get_nowait)
