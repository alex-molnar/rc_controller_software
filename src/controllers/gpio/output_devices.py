from time import sleep
from threading import Thread
from atexit import register

from RPi.GPIO import PWM, OUT, BCM, setup as gpio_setup, setmode as set_gpio_mode, cleanup

set_gpio_mode(BCM)

# TODO: gpiozero is included at the moment, which calls GPIO.cleanup, but when it will be removed, the next line should be uncommented
# register(GPIO.cleanup)


class GeneralPurposeOutputDevice:

    def __init__(self, pin: int, starting_value: float = 0, max_value: float = 1):
        assert 0.1 <= max_value <= 1
        assert 0 <= starting_value <= max_value
        gpio_setup(pin, OUT)
        self._value = starting_value
        self._device = PWM(pin, 50)
        self._device.start(self._value * 100)
        self._max_value = max_value
        self._is_active_background = False

    def __del__(self):
        self._device.stop()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value: float):
        assert 0 <= new_value <= self._max_value
        self._value = new_value
        self._device.ChangeDutyCycle(self._value * 100)
        self._is_active_background = False

    def on(self):
        self.value = self._max_value

    def off(self):
        self.value = 0


class Buzzer(GeneralPurposeOutputDevice):

    def __init__(self, pin: int, starting_value: float = 0, max_value: float = 1):
        super().__init__(pin, starting_value, max_value)
        self._is_active = not self._value == 0

    @property
    def is_active(self):
        return self._is_active

    def buzz(self, seconds: float = 1):
        assert seconds > 0
        try:
            self._is_active = True
            self.on()
            sleep(seconds)
        finally:
            self.off()
            self._is_active = True

    def on(self):
        self._is_active = True
        super().on()

    def off(self):
        self._is_active = False
        super().off()


class LED(GeneralPurposeOutputDevice):

    INF = -1

    def __init__(self, pin: int, starting_value: float = 0, max_value: float = 1):
        super().__init__(pin, starting_value, max_value)

    def _active_sleep(self, seconds):
        int_seconds = int(seconds // 1 * 100)
        int_deciseconds = int(seconds % 1 * 10 // 1 * 10)
        for _ in range(int_seconds + int_deciseconds):
            if not self._is_active_background:
                break
            sleep(0.01)

    def blink(self, times=1, on_time=0.5, off_time=0.5, fade_in_time=1, fade_out_time=1, non_blocking=False):
        assert times == self.INF or 1 <= times
        assert 0 <= on_time
        assert 0 <= off_time
        assert 0 < fade_in_time
        assert 0 < fade_out_time

        self._is_active_background = True

        if non_blocking:
            Thread(target=self.blink, args=(times, on_time, off_time, fade_in_time, fade_out_time)).start()
        else:
            counter = 0
            upper_bound = int(self._max_value * 100)
            self._value = 0

            while self._is_active_background:
                for _ in range(0, upper_bound):
                    if not self._is_active_background:
                        break

                    new_value = self.value + 0.01
                    if new_value > 1:
                        new_value = 1

                    self._value = new_value
                    self._device.ChangeDutyCycle(self._value * 100)

                    sleep(fade_in_time/upper_bound)

                self._active_sleep(on_time)

                for _ in range(upper_bound, 0, -1):
                    if not self._is_active_background:
                        break

                    new_value = self.value - 0.01
                    if new_value < 0:
                        new_value = 0

                    self._value = new_value
                    self._device.ChangeDutyCycle(self._value * 100)

                    sleep(fade_out_time/upper_bound)

                counter += 1
                if times == self.INF or counter < times:
                    self._active_sleep(off_time)
                else:
                    self._is_active_background = False


class StatusLED:

    RED = (255, 0, 255)
    GREEN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PINK = (220, 0, 255)
    PURPLE = (150, 0, 255)
    CYAN = (0, 180, 255)
    ORANGE = (230, 255, 255)
    YELLOW = (180, 255, 255)

    def __init__(self, red_pin, green_pin, start_red_value=0, start_green_value=0):
        self.red_leg = LED(red_pin)
        self.green_leg = LED(green_pin)

        self.red_leg.value = start_red_value / 255
        self.green_leg.value = start_green_value / 255
        self._color = (start_red_value, start_green_value, 255)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        assert isinstance(value, tuple)
        assert len(value) == 3
        assert 0 <= value[0] <= 255
        assert 0 <= value[1] <= 255
        self._color = value
        self.red_leg.value = value[0] / 255
        self.green_leg.value = value[1] / 255


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
        self._angle = (initial_angle + 90) / 18 + 2
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
