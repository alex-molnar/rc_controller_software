from unittest import TestCase
from unittest.mock import MagicMock, patch


import controllers.lighting
from mocks import LEDMock
from collections import defaultdict


R_INDICATOR = 'right_indicator'
L_INDICATOR = 'left_indicator'
HAZARD_WARNING = 'hazard_warning'
LIGHTS = 'lights'
BACKWARD = 'backward'

INDICATORS_OFF = 0
HAZARD_ON = 1
RIGHT_ON = 2
LEFT_ON = 3


@patch('controllers.lighting.LED', return_value=LEDMock())
class TestLighting(TestCase):

    def setup(self):
        self.lights = controllers.lighting.Lights([1,2], [1,2], 1, 2)
        self.lights.logger.debug = MagicMock()
        self.lights.logger.info = MagicMock()
        self.lights.logger.warning = MagicMock()
        self.lights.logger.error = MagicMock()

    def test_setup(self, _):
        self.setup()
        for light in [*self.lights.front_lights, *self.lights.back_lights, self.lights.left_indicator, self.lights.right_indicator]:
            self.assertTrue(light.super_called)
        self.assertFalse(self.lights.light_state)
        self.assertEqual(INDICATORS_OFF, self.lights.indicator_state)

    def test_light_toggle(self, _):
        self.setup()
        self.lights.toggle_lights = MagicMock()
        self.lights.handle_lights(defaultdict(bool, {LIGHTS: False}))
        self.lights.toggle_lights.assert_not_called()
        self.lights.handle_lights(defaultdict(bool, {LIGHTS: True}))
        self.lights.toggle_lights.assert_called()
        self.lights.handle_lights(defaultdict(bool, {LIGHTS: False}))
        self.lights.toggle_lights.assert_called()

    def test_from_OFF_to_RIGHT(self, _):
        self.setup()
        self.lights.turn_right_indicator_on = MagicMock()
        self.lights.handle_lights(defaultdict(bool, {R_INDICATOR: True, HAZARD_WARNING: False}))
        self.assertEqual(RIGHT_ON, self.lights.indicator_state)
        self.lights.turn_right_indicator_on.assert_called()

    def test_from_OFF_to_LEFT(self, _):
        self.setup()
        self.lights.turn_left_indicator_on = MagicMock()
        self.lights.handle_lights(defaultdict(bool, {L_INDICATOR: True, R_INDICATOR: False, HAZARD_WARNING: False}))
        self.assertEqual(LEFT_ON, self.lights.indicator_state)
        self.lights.turn_left_indicator_on.assert_called()

    def test_from_OFF_to_HAZARD(self, _):
        self.setup()
        self.lights.turn_hazard_warning_on = MagicMock()
        self.lights.handle_lights(defaultdict(bool, {HAZARD_WARNING: True}))
        self.assertEqual(HAZARD_ON, self.lights.indicator_state)
        self.lights.turn_hazard_warning_on.assert_called()

    def test_from_RIGHT_to_OFF(self, _):
        self.setup()
        self.lights.turn_indicators_off = MagicMock()
        self.lights.indicator_state = RIGHT_ON
        self.lights.handle_lights(defaultdict(bool, {R_INDICATOR: False, L_INDICATOR: False, HAZARD_WARNING: False}))
        self.assertEqual(INDICATORS_OFF, self.lights.indicator_state)
        self.lights.turn_indicators_off.assert_called()

    def test_from_LEFT_to_OFF(self, _):
        self.setup()
        self.lights.turn_indicators_off = MagicMock()
        self.lights.indicator_state = LEFT_ON
        self.lights.handle_lights(defaultdict(bool,{R_INDICATOR: False, L_INDICATOR: False, HAZARD_WARNING: False}))
        self.assertEqual(INDICATORS_OFF, self.lights.indicator_state)
        self.lights.turn_indicators_off.assert_called()

    def test_from_HAZARD_to_OFF(self, _):
        self.setup()
        self.lights.turn_indicators_off = MagicMock()
        self.lights.indicator_state = HAZARD_ON
        self.lights.handle_lights(defaultdict(bool, {R_INDICATOR: False, L_INDICATOR: False, HAZARD_WARNING: False}))
        self.assertEqual(INDICATORS_OFF, self.lights.indicator_state)
        self.lights.turn_indicators_off.assert_called()

    def test_from_RIGHT_to_LEFT(self, _):
        self.setup()
        self.lights.turn_left_indicator_on = MagicMock()
        self.lights.indicator_state = RIGHT_ON
        self.lights.handle_lights(defaultdict(bool, {L_INDICATOR: True, HAZARD_WARNING: False}))
        self.lights.turn_left_indicator_on.assert_called()

    def test_from_LEFT_to_RIGHT(self, _):
        self.setup()
        self.lights.turn_right_indicator_on = MagicMock()
        self.lights.indicator_state = LEFT_ON
        self.lights.handle_lights(defaultdict(bool, {R_INDICATOR: True, HAZARD_WARNING: False}))
        self.lights.turn_right_indicator_on.assert_called()

    def test_from_RIGHT_to_HAZARD(self, _):
        self.setup()
        self.lights.turn_hazard_warning_on = MagicMock()
        self.lights.indicator_state = RIGHT_ON
        self.lights.handle_lights(defaultdict(bool, {HAZARD_WARNING: True}))
        self.lights.turn_hazard_warning_on.assert_called()

    def test_from_LEFT_to_HAZARD(self, _):
        self.setup()
        self.lights.turn_hazard_warning_on = MagicMock()
        self.lights.indicator_state = LEFT_ON
        self.lights.handle_lights(defaultdict(bool, {HAZARD_WARNING: True}))
        self.lights.turn_hazard_warning_on.assert_called()
