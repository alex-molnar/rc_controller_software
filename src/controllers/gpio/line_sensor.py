from multiprocessing import Process
from time import sleep

from RPi.GPIO import IN, setup as gpio_setup, input as gpio_input

DETECTED = 0
UNDETECTED = 1


class LineSensor:

    def __init__(self, pin, on_line_detected, on_line_undetected):
        gpio_setup(pin, IN)
        self.pin = pin

        self.event_functions = {
            DETECTED: on_line_detected,
            UNDETECTED: on_line_undetected
        }

        self.poll_process = Process(target=self.__poll)
        self.poll_process.start()

    def finish(self):
        self.poll_process.terminate()

    def __poll(self):
        state = gpio_input(self.pin)

        while True:
            new_state = gpio_input(self.pin)

            if new_state != state:
                state = new_state
                self.event_functions[new_state]()

            sleep(0.01)
