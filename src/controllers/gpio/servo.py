from time import sleep

from RPi.GPIO import setup as gpio_setup, PWM, OUT


class Servo:
    """
    Class to controll the servo motor
    """

    def __init__(self, pin, initial_angle=0, min_duty=2, max_duty=12):
        assert min_duty < max_duty
        gpio_setup(pin, OUT)
        self._min_duty = min_duty
        self._max_duty = max_duty
        self._scale_number = 180 / (self._max_duty - self._min_duty)
        self._servo = PWM(pin, 50)
        self._servo.start(0)
        self._angle = (initial_angle + 95) / self._scale_number + self._min_duty  # see at angle
        self._servo.ChangeDutyCycle(self._angle)
        sleep(0.5)

    def __del__(self):
        self._servo.stop()

    @property
    def angle(self):
        return (self._angle - self._min_duty) * self._scale_number - 90

    @angle.setter
    def angle(self, value):
        assert -90 <= value <= 90
        self._angle = (value + 95) / self._scale_number + self._min_duty  # 95 because the inaccuracy of hardware
        self._servo.ChangeDutyCycle(self._angle)

    @property
    def min_duty(self):
        return self._min_duty

    @min_duty.setter
    def min_duty(self, value):
        assert 0 <= value <= 100
        assert value < self._max_duty
        self._min_duty = value
        self._scale_number = 180 / (self._max_duty - self._min_duty)

    @property
    def max_duty(self):
        return self._max_duty

    @max_duty.setter
    def max_duty(self, value):
        assert 0 <= value <= 100
        assert self._min_duty < value
        self._max_duty = value
        self._scale_number = 180 / (self._max_duty - self._min_duty)

    def min(self):
        self._angle = self._min_duty
        self._servo.ChangeDutyCycle(self._angle)

    def max(self):
        self._angle = self._max_duty
        self._servo.ChangeDutyCycle(self._angle)

    def mid(self):
        self._angle = (self._min_duty + self._max_duty) / 2
        self._servo.ChangeDutyCycle(self._angle)

    def left(self):
        self.angle = 15

    def right(self):
        self.angle = -15

    def forward(self):
        self.angle = 0
