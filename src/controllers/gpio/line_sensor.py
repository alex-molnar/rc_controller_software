from multiprocessing import Process
from time import sleep
from typing import Callable

from RPi.GPIO import IN, setup as gpio_setup, input as gpio_input

DETECTED = 0


class LineSensor:

    def __init__(self, pin: int, on_line_changed: Callable[[bool], None]):
        gpio_setup(pin, IN)
        self.pin = pin

        self.on_line_changed = on_line_changed
        self.poll_process = Process(target=self.__poll)
        self.poll_process.start()

    def finish(self) -> None:
        self.poll_process.terminate()

    def __poll(self) -> None:
        state = gpio_input(self.pin)

        while True:
            new_state = gpio_input(self.pin)

            if new_state != state:
                state = new_state
                self.on_line_changed(state == DETECTED)

            sleep(0.01)
