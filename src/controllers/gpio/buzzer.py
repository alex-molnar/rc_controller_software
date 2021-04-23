from time import sleep

from output_device import GeneralPurposeOutputDevice


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