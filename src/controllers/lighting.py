from collections import defaultdict
from logging import getLogger
from typing import List, ItemsView, Any, Dict

from controllers.gpio.leds import LED

R_INDICATOR = 'right_indicator'
L_INDICATOR = 'left_indicator'
HAZARD_WARNING = 'hazard_warning'
LIGHTS = 'lights'
BACKWARD = 'backward'

LIGHTS_OFF = 0
LIGHTS_ON = 1
HAZARD_ON = 2
RIGHT_ON = 3
LEFT_ON = 4


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

        self.private_states = defaultdict(bool)
        self.public_states = defaultdict(bool)

        self.state = LIGHTS_OFF

        self.breaking = False
        self.logger = getLogger('rc_controller')

    def handle_lights(self, data: Dict[str, bool]) -> None:
        if self.state == LIGHTS_OFF:
            if data[LIGHTS]:
                self.__to_li_on()
                self.__turn_lights_on()
        elif not data[LIGHTS]:
            self.__to_li_off()
            self.__turn_lights_off()
        elif self.state == LIGHTS_ON:
            if data[HAZARD_WARNING]:
                self.__to_ha_on()
            elif data[R_INDICATOR]:
                self.__to_ri_on()
            elif data[L_INDICATOR]:
                self.__to_le_on()
        elif self.state == HAZARD_ON:
            if not data[HAZARD_WARNING]:
                self.__to_li_on()
        elif self.state == RIGHT_ON:
            if data[HAZARD_WARNING]:
                self.__to_ha_on()
            elif data[L_INDICATOR]:
                self.__to_le_on()
            elif not data[R_INDICATOR]:
                self.__to_li_on()
        elif self.state == LEFT_ON:
            if data[HAZARD_WARNING]:
                self.__to_ha_on()
            elif data[R_INDICATOR]:
                self.__to_ri_on()
            elif not data[L_INDICATOR]:
                self.__to_li_on()

        if self.private_states[L_INDICATOR] != self.public_states[L_INDICATOR]:
            self.__toggle_left_indicator()
            self.private_states[L_INDICATOR] = self.public_states[L_INDICATOR]

        if self.private_states[R_INDICATOR] != self.public_states[R_INDICATOR]:
            self.__toggle_right_indicator()
            self.private_states[R_INDICATOR] = self.public_states[R_INDICATOR]

        if self.private_states[HAZARD_WARNING] != self.public_states[HAZARD_WARNING]:
            self.__syncronize_indicators()
            self.private_states[HAZARD_WARNING] = self.public_states[HAZARD_WARNING]

        if self.state != LIGHTS_OFF and self.breaking != data[BACKWARD]:
            for light in self.back_lights:
                light.value = 1 if data[BACKWARD] else 0.1
            self.breaking = data[BACKWARD]

    def get_data(self) -> ItemsView[Any, bool]:
        return self.public_states.items()

    def __to_li_off(self) -> None:
        self.logger.debug('Lights turned off')
        self.state = LIGHTS_OFF
        self.public_states[LIGHTS] = False
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = False

    def __to_li_on(self) -> None:
        self.logger.debug('Lights turned on')
        self.state = LIGHTS_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = False

    def __to_ri_on(self) -> None:
        self.logger.debug('Right indicator turned on')
        self.state = RIGHT_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = True
        self.public_states[L_INDICATOR] = False

    def __to_le_on(self) -> None:
        self.logger.debug('Left indicator turned on')
        self.state = LEFT_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = True

    def __to_ha_on(self) -> None:
        self.logger.debug('Hazard warning turned on')
        self.state = HAZARD_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = True
        self.public_states[R_INDICATOR] = True
        self.public_states[L_INDICATOR] = True

    def __turn_lights_on(self) -> None:
        for light in self.front_lights:
            light.on()

        for light in self.back_lights:
            light.on()
            light.value = 0.1

    def __turn_lights_off(self) -> None:
        for light in [*self.front_lights, *self.back_lights]:
            light.off()

    def __toggle_left_indicator(self) -> None:
        if self.private_states[L_INDICATOR]:
            self.left_indicator.off()
        else:
            self.left_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)

    def __toggle_right_indicator(self) -> None:
        if self.private_states[R_INDICATOR]:
            self.right_indicator.off()
        else:
            self.right_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)

    def __syncronize_indicators(self) -> None:
        if not self.private_states[HAZARD_WARNING]:
            self.right_indicator.off()
            self.left_indicator.off()
            self.right_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)
            self.left_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)
