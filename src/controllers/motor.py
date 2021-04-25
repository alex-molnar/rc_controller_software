from threading import Thread
from time import sleep
from collections import defaultdict
from logging import getLogger
from typing import List, Dict, ItemsView, Any

from controllers.gpio.wheel import Wheel
from controllers.gpio.servo import Servo


FORWARD = 'forward'
BACKWARD = 'backward'
LEFT = 'turn_left'
RIGHT = 'turn_right'

REVERSE = 'reverse'
LINE = 'line'

KEEP_CONTAINED = 'keep_contained'
CHANGE_DIRECTION = 'change_direction'
DISTANCE_KEEPING = 'distance_keeping'
LINE_FOLLOWING = 'line_following'

STOP = 0
ACCELERATING = 1
SPEEDING = 2
BREAKING = -1
DISTANCE_STATE = 3
LINE_STATE = 4
CONTAIN_STATE = 5


class Motor:

    MAX_SPEED = 1
    CONTAIN_SPEED = 0.3
    TURN_FORWARD_SPEED = 0.5
    TURN_BACKWARD_SPEED = 0.3
    MAX_DISTANCE = 20
    TURN_DIRECTION = RIGHT

    def __init__(self, right_wheel_pins: List[int], left_wheel_pins: List[int]):
        self.right_wheel = Wheel(*right_wheel_pins)
        self.left_wheel = Wheel(*left_wheel_pins)
        self.servo = Servo(6)

        self.state = STOP
        self.direction = FORWARD

        self.current_speed = 0
        self.servo.forward()

        self.can_accelerate = True
        self.can_break = True

        self.keeping_distance = False
        self.following_line = False
        self.keep_contained = False

        self.distance = 100.0
        self.distance_state = STOP

        self.line_detected = False
        self.contain_state = STOP

        self.states = defaultdict(bool)
        self.logger = getLogger('rc_controller')

    def set_line(self, detected: bool) -> None:
        self.line_detected = detected
        self.states[LINE] = detected
        self.logger.debug(f'Line {"un" if detected else ""}detected')

    def handle_motor_control(self, data: Dict[str, bool]) -> None:
        if data[DISTANCE_KEEPING]:
            if self.state == STOP:
                self.logger.debug('Object avoidance started')
                self.keeping_distance = True
                self.states[DISTANCE_KEEPING] = True
                Thread(target=self.__keep_distance).start()
        elif data[LINE_FOLLOWING]:
            if self.state == STOP:
                self.logger.debug('Line following started')
                self.following_line = True
                self.states[LINE_FOLLOWING] = True
                Thread(target=self.__follow_line).start()
        elif data[KEEP_CONTAINED]:
            if self.state == STOP:
                self.logger.debug('Stop on line started')
                self.keep_contained = True
                self.states[KEEP_CONTAINED] = True
                Thread(target=self.__keep_contained).start()
        elif self.state in [DISTANCE_STATE, LINE_STATE, CONTAIN_STATE]:
            self.states[DISTANCE_KEEPING] = False
            self.states[LINE_FOLLOWING] = False
            self.states[KEEP_CONTAINED] = False
            self.keeping_distance = False
            self.following_line = False
            self.keep_contained = False
            self.logger.debug('Automatic functionality stopped')
        else:
            self.__handle_speed(data)
            self.__handle_directions(data)

    def get_data(self) -> ItemsView[Any, bool]:
        return self.states.items()

    def __keep_distance(self) -> None:
        self.state = DISTANCE_STATE
        self.states[REVERSE] = False
        right_turn = self.TURN_DIRECTION == RIGHT

        if self.distance < self.MAX_DISTANCE:
            self.distance_state = STOP
            if right_turn:
                self.left_wheel.forward(self.TURN_FORWARD_SPEED)
                self.right_wheel.backward(self.TURN_BACKWARD_SPEED)
            else:
                self.left_wheel.backward(self.TURN_BACKWARD_SPEED)
                self.right_wheel.forward(self.TURN_FORWARD_SPEED)
            self.states[self.TURN_DIRECTION] = True
        else:
            self.distance_state = ACCELERATING
            self.right_wheel.forward(self.CONTAIN_SPEED)
            self.left_wheel.forward(self.CONTAIN_SPEED)
            self.current_speed = self.CONTAIN_SPEED
            self.states[FORWARD] = True

        while self.keeping_distance:
            sleep(0.05)
            if self.distance_state == ACCELERATING and self.distance < self.MAX_DISTANCE:
                self.right_wheel.stop()
                self.left_wheel.stop()
                self.current_speed = 0
                self.distance_state = STOP
                self.states[FORWARD] = False

                sleep(0.5)

                if right_turn:
                    self.left_wheel.forward(self.TURN_FORWARD_SPEED)
                    self.right_wheel.backward(self.TURN_BACKWARD_SPEED)
                else:
                    self.left_wheel.backward(self.TURN_BACKWARD_SPEED)
                    self.right_wheel.forward(self.TURN_FORWARD_SPEED)
                self.states[self.TURN_DIRECTION] = True

            elif self.distance_state == STOP and self.distance > self.MAX_DISTANCE:
                self.right_wheel.stop()
                self.left_wheel.stop()
                self.states[self.TURN_DIRECTION] = False

                sleep(0.5)

                self.distance_state = ACCELERATING
                self.right_wheel.forward(self.CONTAIN_SPEED)
                self.left_wheel.forward(self.CONTAIN_SPEED)
                self.current_speed = self.CONTAIN_SPEED
                self.states[FORWARD] = True

        self.states[FORWARD] = False
        self.states[self.TURN_DIRECTION] = False
        self.state = STOP
        self.left_wheel.stop()
        self.right_wheel.stop()
        self.current_speed = 0

    def __follow_line(self) -> None:
        self.state = LINE_STATE
        while self.following_line:
            print(f"Following Line: {self.line_detected}")
            sleep(0.5)
        print('Not Following Line Anymore..')
        self.__stop()

    def __keep_contained(self) -> None:
        self.state = CONTAIN_STATE
        self.states[REVERSE] = False
        right_turn = self.TURN_DIRECTION == RIGHT

        if self.line_detected:
            self.contain_state = STOP
            if right_turn:
                self.left_wheel.forward(self.TURN_FORWARD_SPEED)
                self.right_wheel.backward(self.TURN_BACKWARD_SPEED)
            else:
                self.right_wheel.forward(self.TURN_FORWARD_SPEED)
                self.left_wheel.backward(self.TURN_BACKWARD_SPEED)
            self.states[self.TURN_DIRECTION] = True
            sleep(2.5)
        else:
            self.contain_state = ACCELERATING
            self.right_wheel.forward(self.CONTAIN_SPEED)
            self.left_wheel.forward(self.CONTAIN_SPEED)
            self.current_speed = self.CONTAIN_SPEED
            self.states[FORWARD] = True

        while self.keep_contained:
            sleep(0.05)
            if self.line_detected:
                self.right_wheel.stop()
                self.left_wheel.stop()
                self.current_speed = 0
                self.contain_state = STOP
                self.states[FORWARD] = False

                sleep(0.5)

                if right_turn:
                    self.left_wheel.forward(self.TURN_FORWARD_SPEED)
                    self.right_wheel.backward(self.TURN_BACKWARD_SPEED)
                else:
                    self.right_wheel.forward(self.TURN_FORWARD_SPEED)
                    self.left_wheel.backward(self.TURN_BACKWARD_SPEED)
                self.states[self.TURN_DIRECTION] = True

                sleep(2.5)

            elif self.contain_state == STOP and not self.line_detected:
                self.right_wheel.stop()
                self.left_wheel.stop()
                self.states[self.TURN_DIRECTION] = False

                sleep(0.5)

                self.contain_state = ACCELERATING
                self.right_wheel.forward(self.CONTAIN_SPEED)
                self.left_wheel.forward(self.CONTAIN_SPEED)
                self.current_speed = self.CONTAIN_SPEED
                self.states[FORWARD] = True

        self.states[FORWARD] = False
        self.states[self.TURN_DIRECTION] = False
        self.state = STOP
        self.left_wheel.stop()
        self.right_wheel.stop()
        self.current_speed = 0

    def __handle_speed(self, data: Dict[str, bool]) -> None:
        self.states[REVERSE] = data[REVERSE]

        if self.state == STOP or (self.state in [DISTANCE_STATE, LINE_STATE] and data[FORWARD]):
            if data[BACKWARD]:
                self.states[BACKWARD] = True
            elif data[FORWARD]:
                self.states[FORWARD] = True
                self.states[BACKWARD] = False
                self.can_accelerate = True
                Thread(target=self.__acc).start()
            else:
                self.states[BACKWARD] = False
        elif self.state in [ACCELERATING, DISTANCE_STATE, LINE_STATE]:
            if data[BACKWARD]:
                self.states[FORWARD] = False
                self.states[BACKWARD] = True
                self.can_accelerate = False
                self.__stop()
            elif not data[FORWARD]:
                self.states[FORWARD] = False
                self.can_accelerate = False
                self.can_break = True
                Thread(target=self.__break).start()
        elif self.state == BREAKING:
            if data[BACKWARD]:
                self.states[BACKWARD] = True
                self.can_break = False
                self.__stop()
            elif data[FORWARD]:
                self.states[FORWARD] = True
                self.can_break = False
                self.can_accelerate = True
                Thread(target=self.__acc).start()

    def __handle_directions(self, data: Dict[str, bool]) -> None:
        if (self.direction == RIGHT and not data[RIGHT]) or (self.direction == LEFT and not data[LEFT]):
            self.servo.forward()
            self.direction = FORWARD
            self.states[RIGHT] = False
            self.states[LEFT] = False

        if data[RIGHT]:
            self.servo.right()
            self.direction = RIGHT
            self.states[RIGHT] = True
        elif data[LEFT]:
            self.servo.left()
            self.direction = LEFT
            self.states[LEFT] = True

    def __acc(self) -> None:
        self.state = ACCELERATING

        if self.current_speed < 0.2:
            self.current_speed = 0.2

        while self.can_accelerate and self.current_speed < self.MAX_SPEED:
            if not self.states[REVERSE]:
                self.right_wheel.forward(self.current_speed)
                self.left_wheel.forward(self.current_speed)
            else:
                self.right_wheel.backward(self.current_speed)
                self.left_wheel.backward(self.current_speed)
            sleep(0.1)
            self.current_speed += 0.05

    def __break(self) -> None:
        self.state = BREAKING

        while self.can_break and self.current_speed > 0.2:
            self.current_speed -= 0.05
            if not self.states[REVERSE]:
                self.right_wheel.forward(self.current_speed)
                self.left_wheel.forward(self.current_speed)
            else:
                self.right_wheel.backward(self.current_speed)
                self.left_wheel.backward(self.current_speed)
            sleep(0.1)

        if self.can_break:
            self.right_wheel.stop()
            self.left_wheel.stop()
            self.current_speed = 0
            self.state = STOP

    def __stop(self) -> None:
        self.state = STOP
        self.direction = FORWARD
        self.left_wheel.stop()
        self.right_wheel.stop()
        self.current_speed = 0
