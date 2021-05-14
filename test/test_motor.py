from unittest import TestCase
from unittest.mock import MagicMock, patch

import controllers.motor
from mocks import MotorMock, QueueMock
from collections import defaultdict


controllers.motor.Thread = MagicMock()


FORWARD = 'forward'
BACKWARD = 'backward'
LEFT = 'turn_left'
RIGHT = 'turn_right'

REVERSE = 'reverse'
LINE = 'line'

KEEP_CONTAINED = 'keep_contained'
CHANGE_DIRECTION = 'change_direction'
DISTANCE_KEEPING = 'distance_keeping'

STOP = 0
ACCELERATING = 1
SPEEDING = 2
BREAKING = -1


@patch('controllers.motor.Wheel', return_value=MotorMock())
@patch('controllers.motor.Servo', return_value=MotorMock())
@patch('controllers.motor.Queue', return_value=QueueMock())
class TestMotor(TestCase):

    def setup(self) -> None:
        self.motor = controllers.motor.Motor([1, 2], [1, 2], 1)
        self.motor.logger.debug = MagicMock()
        self.motor.logger.info = MagicMock()
        self.motor.logger.warnig = MagicMock()
        self.motor.logger.error = MagicMock()

    def test_setup(self, _, __, ___):
        self.setup()
        self.assertTrue(self.motor.right_wheel.initialized)
        self.assertTrue(self.motor.left_wheel.initialized)
        self.assertTrue(self.motor.servo.initialized)
        self.assertTrue(self.motor.line_queue.initialized)
        self.motor.servo.forward.assert_called()

    def test_set_line(self, _, __, ___):
        self.setup()
        self.motor.set_line(True)
        self.assertTrue(self.motor.states[LINE])
        self.motor.line_queue.put.assert_called()
        self.motor.set_line(False)
        self.assertFalse(self.motor.states[LINE])

    def test_from_STOP_to_DISTANCE(self, _, __, ___):
        self.setup()
        self.motor.state = STOP
        self.motor.handle_motor_control({DISTANCE_KEEPING: True, KEEP_CONTAINED: False})
        self.assertEqual(DISTANCE_KEEPING, self.motor.state)
        controllers.motor.Thread.assert_called()
        self.motor.state = STOP
        self.motor.handle_motor_control({DISTANCE_KEEPING: True, KEEP_CONTAINED: True})
        self.assertEqual(DISTANCE_KEEPING, self.motor.state)

    def test_from_STOP_to_LINE(self, _, __, ___):
        self.setup()
        self.motor.state = STOP
        self.motor.handle_motor_control({DISTANCE_KEEPING: False, KEEP_CONTAINED: True})
        self.assertEqual(KEEP_CONTAINED, self.motor.state)
        controllers.motor.Thread.assert_called()
        self.motor.state = STOP
        self.motor.handle_motor_control({DISTANCE_KEEPING: True, KEEP_CONTAINED: True})
        self.assertNotEqual(KEEP_CONTAINED, self.motor.state)

    def test_from_DISTANCE_to_STOP(self, _, __, ___):
        self.setup()
        self.motor.state = DISTANCE_KEEPING
        self.motor.handle_motor_control({DISTANCE_KEEPING: False, KEEP_CONTAINED: False})
        self.assertEqual(STOP, self.motor.state)
        self.motor.state = DISTANCE_KEEPING
        self.motor.handle_motor_control({DISTANCE_KEEPING: False, KEEP_CONTAINED: True})
        self.assertNotEqual(STOP, self.motor.state)

    def test_from_LINE_to_STOP(self, _, __, ___):
        self.setup()
        self.motor.state = KEEP_CONTAINED
        self.motor.handle_motor_control({DISTANCE_KEEPING: False, KEEP_CONTAINED: False})
        self.assertEqual(STOP, self.motor.state)
        self.motor.state = KEEP_CONTAINED
        self.motor.handle_motor_control({DISTANCE_KEEPING: True, KEEP_CONTAINED: False})
        self.assertNotEqual(STOP, self.motor.state)

    def test_from_DISTANCE_to_LINE(self, _, __, ___):
        self.setup()
        self.motor.state = DISTANCE_KEEPING
        self.motor.handle_motor_control({DISTANCE_KEEPING: False, KEEP_CONTAINED: True})
        self.assertEqual(KEEP_CONTAINED, self.motor.state)
        self.motor.state = DISTANCE_KEEPING
        self.motor.handle_motor_control({DISTANCE_KEEPING: False, KEEP_CONTAINED: False})
        self.assertNotEqual(KEEP_CONTAINED, self.motor.state)

    def test_from_LINE_to_DISTANCE(self, _, __, ___):
        self.setup()
        self.motor.state = KEEP_CONTAINED
        self.motor.handle_motor_control({DISTANCE_KEEPING: True, KEEP_CONTAINED: False})
        self.assertEqual(DISTANCE_KEEPING, self.motor.state)
        self.motor.state = KEEP_CONTAINED
        self.motor.handle_motor_control({DISTANCE_KEEPING: False, KEEP_CONTAINED: False})
        self.assertNotEqual(DISTANCE_KEEPING, self.motor.state)

    def test_from_STOP_to_ACCELERATING(self, _, __, ___):
        self.setup()
        self.motor.state = STOP
        self.motor.handle_motor_control(defaultdict(bool, {FORWARD: True, BACKWARD: False}))
        self.assertEqual(ACCELERATING, self.motor.state)
        controllers.motor.Thread.assert_called()

    def test_from_ACCELERATING_to_STOP(self, _, __, ___):
        self.setup()
        self.motor.state = ACCELERATING
        self.motor.handle_motor_control(defaultdict(bool, {BACKWARD: True, FORWARD: False}))
        self.assertEqual(STOP, self.motor.state)
        self.motor.state = ACCELERATING
        self.motor.handle_motor_control(defaultdict(bool, {BACKWARD: True, FORWARD: True}))
        self.assertEqual(STOP, self.motor.state)

    def test_from_BREAKING_to_STOP(self, _, __, ___):
        self.setup()
        self.motor.state = BREAKING
        self.motor.handle_motor_control(defaultdict(bool, {BACKWARD: True, FORWARD: False}))
        self.assertEqual(STOP, self.motor.state)
        self.motor.state = BREAKING
        self.motor.handle_motor_control(defaultdict(bool, {BACKWARD: True, FORWARD: True}))
        self.assertEqual(STOP, self.motor.state)

    def test_from_ACCELERATING_to_BREAKING(self, _, __, ___):
        self.setup()
        self.motor.state = ACCELERATING
        self.motor.handle_motor_control(defaultdict(bool, {BACKWARD: False, FORWARD: False}))
        self.assertEqual(BREAKING, self.motor.state)

    def test_from_BREAKING_to_ACCELERATING(self, _, __, ___):
        self.setup()
        self.motor.state = BREAKING
        self.motor.handle_motor_control(defaultdict(bool, {FORWARD: True, BACKWARD: False}))
        self.assertEqual(ACCELERATING, self.motor.state)

    def test_from_FORWARD_to_RIGHT(self, _, __, ___):
        self.setup()
        self.motor.direction = FORWARD
        self.motor.handle_motor_control(defaultdict(bool, {RIGHT: True, LEFT: False}))
        self.assertEqual(RIGHT, self.motor.direction)
        self.motor.servo.right.assert_called()
        self.motor.direction = FORWARD
        self.motor.handle_motor_control(defaultdict(bool, {RIGHT: True, LEFT: True}))
        self.assertNotEqual(RIGHT, self.motor.direction)

    def test_from_FORWARD_to_LEFT(self, _, __, ___):
        self.setup()
        self.motor.direction = FORWARD
        self.motor.handle_motor_control(defaultdict(bool, {LEFT: True}))
        self.assertEqual(LEFT, self.motor.direction)
        self.motor.servo.left.assert_called()

    def test_from_LEFT_to_FORWARD(self, _, __, ___):
        self.setup()
        self.motor.direction = LEFT
        self.motor.handle_motor_control(defaultdict(bool, {LEFT: False, RIGHT: False}))
        self.assertEqual(FORWARD, self.motor.direction)
        self.motor.servo.right.assert_called()

    def test_from_RIGHT_to_FORWARD(self, _, __, ___):
        self.setup()
        self.motor.direction = RIGHT
        self.motor.handle_motor_control(defaultdict(bool, {LEFT: False, RIGHT: False}))
        self.assertEqual(FORWARD, self.motor.direction)
        self.motor.servo.right.assert_called()

    def test_from_LEFT_to_RIGHT(self, _, __, ___):
        self.setup()
        self.motor.direction = LEFT
        self.motor.handle_motor_control(defaultdict(bool, {LEFT: False, RIGHT: True}))
        self.assertEqual(RIGHT, self.motor.direction)
        self.motor.servo.right.assert_called()

    def test_from_RIGHT_to_LEFT(self, _, __, ___):
        self.setup()
        self.motor.direction = RIGHT
        self.motor.handle_motor_control(defaultdict(bool, {LEFT: True, RIGHT: False}))
        self.assertEqual(LEFT, self.motor.direction)
        self.motor.servo.right.assert_called()
