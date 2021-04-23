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
