from threading import Thread
from time import sleep

from RPi.GPIO import IN, setup as gpio_setup, input as gpio_input


class LineSensor:

    def __init__(self, pin):
        self.pin = pin
        gpio_setup(pin, IN)
        self._finished = False
        self.state = gpio_input(self.pin)
        self.on_line_detected = None
        self.on_line_undetected = None
        self.poll_thread = Thread(target=self.__poll)
        self.poll_thread.start()

    def __del__(self):
        self.finish()

    def __poll(self):
        while not self._finished:
            new_state = gpio_input(self.pin)
            if new_state == 1 and self.state == 0:
                self.state = 1
                if self.on_line_undetected is not None:
                    self.on_line_undetected()
            elif new_state == 0 and self.state == 1:
                self.state = 0
                if self.on_line_detected is not None:
                    self.on_line_detected()
            sleep(0.01)

    def get(self):
        return f'Line {"not " if self.state == 1 else ""}detected'

    def finish(self):
        self._finished = True
