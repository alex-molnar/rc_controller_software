from gpiozero import LineSensor, DistanceSensor
from utils.output_devices import Buzzer
from lighting import Lights
from motor import Motor
from collections import defaultdict
from typing import Optional
from utils.constants import * 


class Controller:
    """
    Class that responsible for the functionality of the car. Holds together the components needed to controll the car, and provides a nice, easy-to-use interface.

    :examples:
    >>> control = Controller()
    >>> control.set_values({'forward': True, 'lights': True}) # move the car forward, with the lights on
    >>> dict(control.get_values())
    {"forward": True, "lights": True}
    """

    def __init__(self, pin_numbering=None):
        """
        Initialises the GPIO components, and other controll components

        :Assumptions: None

        :param pin_numbering: ignored, added so it is possible to parse the GPIO pins from file in the future
        """
        # self.buzzer = Buzzer(17)
        # self.lights = Lights([18,22], [20, 21, 26], 23, 27)
        # self.distance_sensor = DistanceSensor(echo=4, trigger=3)
        # self.line_sensor = LineSensor(24)
        # self.motor = Motor([7, 8], [9, 10]) 

        # self.line_sensor.when_line = lambda: self.__set_line(True)
        # self.line_sensor.when_no_line = lambda: self.__set_line(False)

        self.states = defaultdict(bool)

    def __honk(self, horn_pushed: bool) -> None:
        """
        Turns the buzzer on or off respectively.

        :Assumptions: None

        :param horn_pushed: True if the horn button is currently being pushed by the user

        :return: None
        """
        # if horn_pushed and not self.buzzer.is_active:
        #     self.buzzer.on()
        # elif not horn_pushed and self.buzzer.is_active:
        #     self.buzzer.off()
        pass

    def __set_line(self, line_detected: bool) -> None:
        """
        Sets the state of the line detector accordingly

        :Assumptions: None

        :param line_detected: True if line was detected, False, if no line is detected

        :return: None
        """
        # self.states[LINE] = line_detected
        # self.motor.line_detected = line_detected
        pass

    def set_values(self, data: dict):
        """
        Sets the state of the car, and changes behavior if possible, or necessary.

        :Assumpitons: None

        :param data: Contains the data of the user input

        :return: None
        """
        default_data = defaultdict(bool, data)

        if data[FORWARD]:
            print('FORWARD')

        default_data[DISTANCE] = self.states[DISTANCE]
        # self.motor.handle_motor_control(default_data)  
        # default_data[BACKWARD] = self.motor.states[BACKWARD]
        # self.lights.handle_lights(default_data)
        # self.__honk(default_data[HORN])

    def get_values(self) -> dict:
        """
        Sets two additional paramaters, then returns the state of the car.

        :Assumptions: None

        :return: state as key-value pairs
        """
        # for key, value in self.motor.get_data():
        #     self.states[key] = value 
        # for key, value in self.lights.get_data():
        #     self.states[key] = value

        # distance = round(self.distance_sensor.distance * 100, 2)
        # self.states[DISTANCE] = distance
        # self.motor.distance = distance
        # self.states[SPEED] = round(self.motor.current_speed * 3.6 * 10, 2)

        return dict(self.states)
