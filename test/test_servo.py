from unittest import TestCase
from unittest.mock import MagicMock, patch

import controllers.gpio.servo
from mocks import PWMMock


controllers.gpio.servo.gpio_setup = MagicMock()


@patch('controllers.gpio.servo.PWM', return_value=PWMMock())
class TestServo(TestCase):

    PIN = 1
    ANGLE = 45
    MIN_ANGLE = -95
    MAX_ANGLE = 85
    # The Servo can rotate in ~180, but the observation shows that the range is (-95, 85), rather then (-90, 90),
    # since the car has been assembled. If the hardware supports it, it should be (-90, 90), but right now it is
    # correct, and shows the correct values in real life
    MIN_DUTY = 0
    MAX_DUTY = 10

    def setup(self, in_angle=0, min_d=MIN_DUTY, max_d=MAX_DUTY):
        self.servo = controllers.gpio.servo.Servo(self.PIN, initial_angle=in_angle, min_duty=min_d, max_duty=max_d)

    def test_setup(self, _):
        self.setup()
        controllers.gpio.servo.gpio_setup.assert_called_with(self.PIN, 0)
        self.servo._servo.ChangeDutyCycle.assert_called()
        self.servo._servo.start.assert_called_with(0)

    def test_initials(self, _):
        self.setup(self.ANGLE, 5, 15)
        self.assertEqual(self.ANGLE, self.servo.angle)
        self.assertEqual(5, self.servo.min_duty)
        self.assertEqual(15, self.servo.max_duty)

    def test_setup_sanity_checks(self, _):
        self.assertRaises(AssertionError, self.setup, -100, self.MIN_DUTY, self.MAX_DUTY)
        self.assertRaises(AssertionError, self.setup, 100, self.MIN_DUTY, self.MAX_DUTY)
        self.assertRaises(AssertionError, self.setup, self.ANGLE, -1, 50)
        self.assertRaises(AssertionError, self.setup, self.ANGLE, 0, 110)
        self.assertRaises(AssertionError, self.setup, self.ANGLE, 50, 25)

    def test_min_duty_sanity_checks(self, _):
        self.setup()
        self.assertRaises(AssertionError, setattr, self.servo, 'min_duty', -1)
        self.assertRaises(AssertionError, setattr, self.servo, 'min_duty', 150)
        self.assertRaises(AssertionError, setattr, self.servo, 'min_duty', self.MAX_DUTY + 1)

    def test_max_duty_sanity_checks(self, _):
        self.setup()
        self.assertRaises(AssertionError, setattr, self.servo, 'max_duty', -1)
        self.assertRaises(AssertionError, setattr, self.servo, 'max_duty', 150)
        self.assertRaises(AssertionError, setattr, self.servo, 'max_duty', self.MIN_DUTY - 1)

    def test_angle_sanity_checks(self, _):
        self.setup()
        self.assertRaises(AssertionError, setattr, self.servo, 'angle', -100)
        self.assertRaises(AssertionError, setattr, self.servo, 'angle', 100)

    def test_angle_set_correctly(self, _):
        self.setup()
        self.servo.angle = self.ANGLE
        self.assertEqual(self.ANGLE, self.servo.angle)

    def test_min(self, _):
        self.setup()
        self.servo.min()
        self.assertEqual(self.MIN_ANGLE, self.servo.angle)
        self.assertEqual(self.MIN_DUTY, self.servo._angle)
        self.servo._servo.ChangeDutyCycle.assert_called_with(self.MIN_DUTY)

    def test_max(self, _):
        self.setup()
        self.servo.max()
        self.assertEqual(self.MAX_ANGLE, self.servo.angle)
        self.assertEqual(self.MAX_DUTY, self.servo._angle)
        self.servo._servo.ChangeDutyCycle.assert_called_with(self.MAX_DUTY)

    def test_mid(self, _):
        self.setup()
        self.servo.mid()
        self.assertEqual(-5, self.servo.angle)
        self.assertEqual(5, self.servo._angle)
        self.servo._servo.ChangeDutyCycle.assert_called_with(5)

    def test_right(self, _):
        self.setup()
        self.servo.right()
        self.assertEqual(-15, self.servo.angle)
        self.servo._servo.ChangeDutyCycle.assert_called()

    def test_left(self, _):
        self.setup()
        self.servo.left()
        self.assertEqual(15, self.servo.angle)
        self.servo._servo.ChangeDutyCycle.assert_called()

    def test_forward(self, _):
        self.setup()
        self.servo.forward()
        self.assertEqual(0, self.servo.angle)
        self.servo._servo.ChangeDutyCycle.assert_called()
