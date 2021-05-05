from collections import defaultdict
from logging import getLogger
from typing import List, ItemsView, Any, Dict

from controllers.gpio.leds import LED

R_INDICATOR = 'right_indicator'
L_INDICATOR = 'left_indicator'
HAZARD_WARNING = 'hazard_warning'
LIGHTS = 'lights'
BACKWARD = 'backward'

INDICATORS_OFF = 0
HAZARD_ON = 1
RIGHT_ON = 2
LEFT_ON = 3


class Lights:

    def __init__(
            self,
            front_lights_pin: List[int],
            back_lights_pin: List[int],
            left_indicator_pin: int,
            right_indicator_pin: int
    ):
        self.front_lights = [LED(pin) for pin in front_lights_pin]
        self.back_lights = [LED(pin) for pin in back_lights_pin]
        self.right_indicator = LED(right_indicator_pin)
        self.left_indicator = LED(left_indicator_pin)

        for light in [*self.front_lights, *self.back_lights, self.left_indicator, self.right_indicator]:
            light.off()

        self.private_states = defaultdict(bool)
        self.public_states = defaultdict(bool)

        self.light_state = False
        self.indicator_state = INDICATORS_OFF

        self.breaking = False
        self.break_light_value = 0
        self.logger = getLogger('rc_controller')

    def handle_lights(self, data: Dict[str, bool]) -> None:
        if self.light_state != data[LIGHTS]:
            self.toggle_lights()
            self.light_state = data[LIGHTS]
            self.public_states[LIGHTS] = data[LIGHTS]

        if self.indicator_state != HAZARD_ON and data[HAZARD_WARNING]:
            self.turn_hazard_warning_on()
        elif self.indicator_state not in [HAZARD_ON, RIGHT_ON] and data[R_INDICATOR]:
            self.turn_right_indicator_on()
        elif self.indicator_state not in [HAZARD_ON, LEFT_ON] and data[L_INDICATOR]:
            self.turn_left_indicator_on()
        elif not any([data[index] for index in [HAZARD_WARNING, R_INDICATOR, L_INDICATOR]]) or (self.indicator_state == HAZARD_ON and not data[HAZARD_WARNING]):
            self.turn_indicators_off()

        if self.breaking != data[BACKWARD]:
            for light in self.back_lights:
                light.value = 1 if data[BACKWARD] else self.break_light_value
            self.breaking = data[BACKWARD]

    def get_data(self) -> ItemsView[Any, bool]:
        return self.public_states.items()

    def turn_right_indicator_on(self) -> None:
        self.logger.debug('Right indicator turned on')
        self.indicator_state = RIGHT_ON
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = True
        self.public_states[L_INDICATOR] = False
        self.left_indicator.off()
        self.right_indicator.blink(non_blocking=True)

    def turn_left_indicator_on(self) -> None:
        self.logger.debug('Left indicator turned on')
        self.indicator_state = LEFT_ON
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = True
        self.right_indicator.off()
        self.left_indicator.blink(non_blocking=True)

    def turn_hazard_warning_on(self) -> None:
        self.logger.debug('Hazard warning turned on')
        self.indicator_state = HAZARD_ON
        self.public_states[HAZARD_WARNING] = True
        self.public_states[L_INDICATOR] = True
        self.public_states[R_INDICATOR] = True
        self.right_indicator.off()
        self.left_indicator.off()
        self.right_indicator.blink(non_blocking=True)
        self.left_indicator.blink(non_blocking=True)

    def turn_indicators_off(self) -> None:
        self.logger.debug('Hazard warning turned on')
        self.indicator_state = INDICATORS_OFF
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = False
        self.right_indicator.off()
        self.left_indicator.off()

    def toggle_lights(self) -> None:
        self.break_light_value = 0.1 if self.break_light_value == 0 else 0
        for light in [*self.front_lights, *self.back_lights]:
            light.toggle(1 if light in self.front_lights else 0.1)
