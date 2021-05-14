from collections import defaultdict
from logging import getLogger

from controllers.gpio.distance_sensor import DistanceSensor
from controllers.gpio.buzzer import Buzzer
from controllers.lighting import Lights
from controllers.motor import Motor
from controllers.gpio.line_sensor import LineSensor

HORN = 'horn'
DISTANCE = 'distance'
SPEED = 'speed'


class Controller:
    """
    Class that responsible for the functionality of the car. Holds together the components needed to controll the car,
    and provides a nice, easy-to-use interface.

    :examples:
    >>> control = Controller()
    >>> control.set_values({'forward': True, 'lights': True}) # move the car forward, with the lights on
    >>> dict(control.get_values())
    {"forward": True, "lights": True}
    """

    def __init__(self):
        """
        Initialises the GPIO components, and other control components

        :Assumptions: None
        """
        self.buzzer = Buzzer(26)
        self.lights = Lights([4, 17, 18, 27], [24, 25], 22, 23)
        self.motor = Motor([7, 8], [9, 10], 6)
        self.distance_sensor = DistanceSensor(echo=20, trigger=3)
        self.line_sensor = LineSensor(21, self.motor.set_line)

        self.states = defaultdict(bool)
        self.logger = getLogger('rc_controller')

    def __honk(self, horn_pushed: bool) -> None:
        """
        Turns the buzzer on or off respectively.

        :Assumptions: None

        :param horn_pushed: True if the horn button is currently being pushed by the user

        :return: None
        """
        if horn_pushed and not self.buzzer.is_active:
            self.buzzer.on()
            self.logger.debug('Honk started')
        elif not horn_pushed and self.buzzer.is_active:
            self.buzzer.off()
            self.logger.debug('Honk stopped')

    def set_values(self, data: dict) -> None:
        """
        Sets the state of the car, and changes behavior if possible, or necessary.

        :Assumptions: None

        :param data: Contains the data of the user input

        :return: None
        """
        default_data = defaultdict(bool, data)
        self.motor.handle_motor_control(default_data)
        self.lights.handle_lights(default_data)
        self.__honk(default_data[HORN])

    def get_values(self) -> dict:
        """
        Sets two additional paramaters, then returns the state of the car.

        :Assumptions: None

        :return: state as key-value pairs
        """
        for key, value in self.motor.get_data():
            self.states[key] = value
        for key, value in self.lights.get_data():
            self.states[key] = value

        distance = round(self.distance_sensor.distance - 10, 2)
        self.states[DISTANCE] = distance
        self.motor.distance = distance
        self.states[SPEED] = round(self.motor.current_speed * 3.6 * 10, 2)

        return dict(self.states)