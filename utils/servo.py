import RPi.GPIO as gpio
from time import sleep


class Servo:
    """
    Class to controll the servo motor
    """

    def __init__(self, pin, initial_angle=0, min_duty=2, max_duty=12):
        assert min_duty < max_duty
        gpio.setup(pin, gpio.OUT)
        self._min_duty = min_duty
        self._max_duty = max_duty
        self._scale_number = 180 / (self._max_duty - self._min_duty)
        self.servo = gpio.PWM(pin, 50)
        self.servo.start(0)
        self._angle = (initial_angle + 90) / 18 + 2
        self.servo.ChangeDutyCycle(self._angle)
        sleep(0.5)

    def __del__(self):
        self.servo.stop()
        gpio.cleanup()
        print("del ran")

    @property
    def angle(self):
        return (self._angle - self._min_duty) * self._scale_number - 90

    @angle.setter
    def angle(self, value):
        assert -90 <= value <= 90
        self._angle = (value + 90) / self._scale_number + self._min_duty
        self.servo.ChangeDutyCycle(self._angle)

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
        self.servo.ChangeDutyCycle(self._angle)

    def max(self):
        self._angle = self._max_duty
        self.servo.ChangeDutyCycle(self._angle)

    def mid(self):
        self._angle = (self._min_duty + self._max_duty) / 2
        self.servo.ChangeDutyCycle(self._angle)


# GPIO.setup(25, GPIO.OUT)
# pwm = GPIO.PWM(25, 50)
# pwm.start(0)
# duty = 11#145 / 18 + 2
# GPIO.output(25, True)
# pwm.ChangeDutyCycle(duty)
# sleep(1)
# #GPIO.output(25, False)
# #pwm.ChangeDutyCycle(0)
# pwm.stop()
# GPIO.cleanup()

if __name__ == "__main__":

