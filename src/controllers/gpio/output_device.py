from RPi.GPIO import PWM, OUT, setup as gpio_setup


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
        try:
            self._device.stop()
        except AttributeError:
            pass

    @property
    def is_active(self) -> bool:
        return not self._value == 0

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, new_value: float) -> None:
        assert 0 <= new_value <= self._max_value
        self._value = new_value
        self._device.ChangeDutyCycle(self._value * 100)
        self._is_active_background = False

    def on(self, value: float = 1) -> None:
        self.value = value

    def off(self) -> None:
        self.value = 0

    def toggle(self, value: float = 1) -> None:
        if self.is_active:
            self.off()
        else:
            self.on(value)
