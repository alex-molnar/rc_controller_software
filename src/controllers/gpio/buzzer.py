from time import sleep

from controllers.gpio.output_device import GeneralPurposeOutputDevice


class Buzzer(GeneralPurposeOutputDevice):

    def __init__(self, pin: int, starting_value: float = 0, max_value: float = 1):
        super().__init__(pin, starting_value, max_value)

    def buzz(self, seconds: float = 1) -> None:
        assert seconds > 0
        try:
            self.on()
            sleep(seconds)
        finally:
            self.off()
