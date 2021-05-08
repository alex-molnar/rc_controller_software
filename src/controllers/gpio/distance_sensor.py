from logging import getLogger
from time import sleep, time

from RPi.GPIO import OUT, IN, HIGH, LOW, input as gpio_input, output, setup


speed_of_sound = 34300


class DistanceSensor:
    def __init__(self, echo: int, trigger: int):
        self.echo = echo
        self.trigger = trigger
        setup(self.echo, IN)
        setup(self.trigger, OUT)
        output(self.trigger, HIGH)
        sleep(2)
        self._distance = 200.0
        self.logger = getLogger('rc_controller')

    @property
    def distance(self):
        output(self.trigger, HIGH)
        sleep(0.00001)
        output(self.trigger, LOW)

        measure_start = None
        measure_stop = None
        echo_received = True

        start = time()
        while gpio_input(self.echo) == LOW:
            measure_start = time()
            if measure_start - start > 0.2:
                echo_received = False
                break

        start = time()
        while gpio_input(self.echo) == HIGH:
            measure_stop = time()
            if measure_stop - start > 0.2:
                echo_received = False
                break

        if not echo_received or measure_start is None or measure_stop is None:
            self.logger.warning('No echo received from distance sensor')
            return self._distance
        return speed_of_sound * (measure_stop - measure_start) / 2
