from RPi.GPIO import PWM, OUT, setup
from time import sleep
from threading import Thread
from atexit import register
# TODO: why is GPIO included twice?
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

# TODO: gpiozero is included at the moment, which calls GPIO.cleanup, but when it will be removed, the next line should
# be uncommented
# register(GPIO.cleanup)


class GeneralPurposeOutputDevice:

    def __init__(self, pin: int, starting_value: float = 0, max_value: float = 1):
        assert 0.1 <= max_value <= 1
        assert 0 <= starting_value <= max_value
        setup(pin, OUT)
        self._value = starting_value
        self._device = PWM(pin, 50)
        self._device.start(self._value * 100)
        self._max_value = max_value
        self._is_active_background = False

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

    def __init__(self, pin: int, starting_value: float=0, max_value: float=1):
        super().__init__(pin, starting_value, max_value)
        self._is_active = not self._value == 0

    @property
    def is_active(self):
        return self._is_active

    def buzz(self, seconds: float=1):
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

    def __init__(self, pin: int, starting_value: float=0, max_value: float=1):
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

            while(self._is_active_background):
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


if __name__ == "__main__":
    l = LED(20)
    l.blink(times=2)