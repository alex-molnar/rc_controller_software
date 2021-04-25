from time import sleep

from RPi.GPIO import setup as gpio_setup, PWM, OUT


class Servo:
    """
    Class to controll the servo motor
    """

    def __init__(self, pin: int, initial_angle: int = 0, min_duty: int = 2, max_duty: int = 12):
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
    def angle(self) -> float:
        return (self._angle - self._min_duty) * self._scale_number - 90

    @angle.setter
    def angle(self, value: int) -> None:
        assert -90 <= value <= 90
        self._angle = (value + 95) / self._scale_number + self._min_duty  # 95 because the inaccuracy of hardware
        self._servo.ChangeDutyCycle(self._angle)

    @property
    def min_duty(self) -> int:
        return self._min_duty

    @min_duty.setter
    def min_duty(self, value: int) -> None:
        assert 0 <= value <= 100
        assert value < self._max_duty
        self._min_duty = value
        self._scale_number = 180 / (self._max_duty - self._min_duty)

    @property
    def max_duty(self) -> int:
        return self._max_duty

    @max_duty.setter
    def max_duty(self, value: int) -> None:
        assert 0 <= value <= 100
        assert self._min_duty < value
        self._max_duty = value
        self._scale_number = 180 / (self._max_duty - self._min_duty)

    def min(self) -> None:
        self._angle = self._min_duty
        self._servo.ChangeDutyCycle(self._angle)

    def max(self) -> None:
        self._angle = self._max_duty
        self._servo.ChangeDutyCycle(self._angle)

    def mid(self) -> None:
        self._angle = (self._min_duty + self._max_duty) / 2
        self._servo.ChangeDutyCycle(self._angle)

    def left(self) -> None:
        self.angle = 15

    def right(self) -> None:
        self.angle = -15

    def forward(self) -> None:
        self.angle = 0
