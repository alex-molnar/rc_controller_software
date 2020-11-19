from utils.output_devices import LED
from collections import defaultdict
from utils.constants import *


class Lights:

    def __init__(self, front_lights_pin, back_lights_pin, left_indicator_pin, right_indicator_pin):
        self.front_lights = [ LED(pin) for pin in front_lights_pin ]
        self.back_lights = [ LED(pin) for pin in back_lights_pin ]
        self.right_indicator = LED(right_indicator_pin)
        self.left_indicator = LED(left_indicator_pin)

        self.private_states = defaultdict(bool)
        self.public_states = defaultdict(bool)

        self.state = LIGHTS_OFF

        self.breaking = False

    def handle_lights(self, data):
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

        if self.state != LIGHTS_OFF and self.breaking != data['backward']:
            for light in self.back_lights:
                light.value = 1 if data['backward'] else 0.1  # TODO: constant
            self.breaking = data['backward']

    def get_data(self):
        return self.public_states.items()

    def __to_li_off(self):
        self.state = LIGHTS_OFF
        self.public_states[LIGHTS] = False
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = False

    def __to_li_on(self):
        self.state = LIGHTS_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = False

    def __to_ri_on(self):
        self.state = RIGHT_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = True
        self.public_states[L_INDICATOR] = False

    def __to_le_on(self):
        self.state = LEFT_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = False
        self.public_states[R_INDICATOR] = False
        self.public_states[L_INDICATOR] = True

    def __to_ha_on(self):
        self.state = HAZARD_ON
        self.public_states[LIGHTS] = True
        self.public_states[HAZARD_WARNING] = True
        self.public_states[R_INDICATOR] = True
        self.public_states[L_INDICATOR] = True

    def __turn_lights_on(self):
        for light in self.front_lights:
            light.on()

        for light in self.back_lights:
            light.on()
            light.value = 0.1

    def __turn_lights_off(self):
        for light in [*self.front_lights, *self.back_lights]:
            light.off()

    def __toggle_left_indicator(self):
        if self.private_states[L_INDICATOR]:
            self.left_indicator.off()
        else:
            self.left_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)

    def __toggle_right_indicator(self):
        if self.private_states[R_INDICATOR]:
            self.right_indicator.off()
        else:
            self.right_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)

    def __syncronize_indicators(self):
        if not self.private_states[HAZARD_WARNING]:
            self.right_indicator.off()
            self.left_indicator.off()
            self.right_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)
            self.left_indicator.blink(times=LED.INF, on_time=0.3, off_time=0, fade_in_time=0.5, fade_out_time=0.5, non_blocking=True)
