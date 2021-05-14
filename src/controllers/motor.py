from threading import Thread
from time import sleep
from collections import defaultdict
from logging import getLogger
from typing import List, Dict, ItemsView, Any
from multiprocessing import Queue
from queue import Empty

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

STOP = 0
ACCELERATING = 1
SPEEDING = 2
BREAKING = -1


class Motor:

    MAX_SPEED = 1
    AUTO_SPEED = 0.3
    MAX_DISTANCE = 25

    def __init__(self, right_wheel_pins: List[int], left_wheel_pins: List[int], servo_pin: int):
        self.right_wheel = Wheel(*right_wheel_pins)
        self.left_wheel = Wheel(*left_wheel_pins)
        self.servo = Servo(servo_pin)

        self.state = STOP
        self.direction = FORWARD

        self.current_speed = 0
        self.servo.forward()

        self.can_accelerate = True
        self.can_break = True

        self.distance = 100.0

        self.line_detected = False
        self.line_queue = Queue()
        self.contain_state = STOP

        self.states = defaultdict(bool)
        self.logger = getLogger('rc_controller')

    def set_line(self, detected: bool) -> None:
        if detected:
            self.line_queue.put("detected")
        self.states[LINE] = detected
        self.logger.debug(f'Line {"" if detected else "un"}detected')

    def auto_func_condition(self) -> bool:
        if self.state == DISTANCE_KEEPING:
            return self. distance < self.MAX_DISTANCE
        elif self.state == KEEP_CONTAINED:
            try:
                self.line_queue.get_nowait()
                return True
            except Empty:
                return False

    def clear_queue(self) -> None:
        try:
            while True:
                self.line_queue.get_nowait()
        except Empty:
            pass

    def handle_motor_control(self, data: Dict[str, bool]) -> None:
        if data[DISTANCE_KEEPING]:
            if self.state in [STOP, KEEP_CONTAINED]:
                self.logger.debug('Object avoidance started')
                self.state = DISTANCE_KEEPING
                self.states[DISTANCE_KEEPING] = True
                Thread(target=self.auto_functionality, args=(DISTANCE_KEEPING,)).start()
        elif data[KEEP_CONTAINED]:
            if self.state in [STOP, DISTANCE_KEEPING]:
                self.logger.debug('Stop on line started')
                self.state = KEEP_CONTAINED
                self.states[KEEP_CONTAINED] = True
                self.clear_queue()
                Thread(target=self.auto_functionality, args=(KEEP_CONTAINED,)).start()
        elif self.state in [DISTANCE_KEEPING, KEEP_CONTAINED]:
            self.logger.debug(f'{self.state} functionality stopped')
            self.states[self.state] = False
            self.state = STOP
        else:
            self.__handle_speed(data)
            self.__handle_directions(data)

    def get_data(self) -> ItemsView[Any, bool]:
        return self.states.items()

    def auto_functionality(self, auto_type: str) -> None:
        self.states[FORWARD] = True
        for state in [BACKWARD, RIGHT, LEFT, REVERSE]:
            self.states[state] = False
        self.left_wheel.forward(self.AUTO_SPEED)
        self.right_wheel.forward(self.AUTO_SPEED)
        self.current_speed = self.AUTO_SPEED

        turning_count = -1

        while self.states[auto_type]:
            sleep(0.05)
            if self.auto_func_condition():
                self.right_wheel.stop()
                self.left_wheel.stop()
                self.servo.forward()
                self.current_speed = 0
                self.states[FORWARD] = False
                self.states[BACKWARD] = True
                self.current_speed = 0

                sleep(0.5)

                self.states[BACKWARD] = False
                self.states[REVERSE] = True
                self.states[FORWARD] = True
                self.left_wheel.backward(self.AUTO_SPEED)
                self.right_wheel.backward(self.AUTO_SPEED)
                self.current_speed = self.AUTO_SPEED

                sleep(1.5)

                self.states[BACKWARD] = True
                self.states[FORWARD] = False
                self.states[REVERSE] = False
                self.left_wheel.stop()
                self.right_wheel.stop()
                self.current_speed = 0

                sleep(0.5)

                self.states[RIGHT] = True
                self.states[FORWARD] = True
                self.states[BACKWARD] = False
                self.servo.right()
                self.left_wheel.forward(self.AUTO_SPEED)
                self.right_wheel.forward(self.AUTO_SPEED)
                self.clear_queue()
                self.current_speed = self.AUTO_SPEED
                turning_count = 1
            elif turning_count > 30:
                turning_count = -1
                self.states[RIGHT] = False
                self.servo.forward()
            elif turning_count > 0:
                turning_count += 1

        for state in [FORWARD, BACKWARD, RIGHT, LEFT, REVERSE]:
            self.states[state] = False

        self.state = STOP
        self.left_wheel.stop()
        self.right_wheel.stop()
        self.servo.forward()
        self.current_speed = 0

    def __handle_speed(self, data: Dict[str, bool]) -> None:
        self.states[REVERSE] = data[REVERSE]

        if self.state == STOP:
            if data[BACKWARD]:
                self.states[BACKWARD] = True
            elif data[FORWARD]:
                self.states[FORWARD] = True
                self.states[BACKWARD] = False
                self.can_accelerate = True
                self.state = ACCELERATING
                Thread(target=self.__acc).start()
            else:
                self.states[BACKWARD] = False
        elif self.state == ACCELERATING:
            if data[BACKWARD]:
                self.states[FORWARD] = False
                self.states[BACKWARD] = True
                self.can_accelerate = False
                self.state = STOP
                self.__stop()
            elif not data[FORWARD]:
                self.states[FORWARD] = False
                self.can_accelerate = False
                self.can_break = True
                self.state = BREAKING
                Thread(target=self.__break).start()
        elif self.state == BREAKING:
            if data[BACKWARD]:
                self.states[BACKWARD] = True
                self.can_break = False
                self.state = STOP
                self.__stop()
            elif data[FORWARD]:
                self.states[FORWARD] = True
                self.can_break = False
                self.can_accelerate = True
                self.state = ACCELERATING
                Thread(target=self.__acc).start()

    def __handle_directions(self, data: Dict[str, bool]) -> None:
        if (self.direction == RIGHT and not data[RIGHT]) or (self.direction == LEFT and not data[LEFT]):
            self.servo.forward()
            self.direction = FORWARD
            self.states[RIGHT] = False
            self.states[LEFT] = False

        if data[LEFT]:
            self.servo.left()
            self.direction = LEFT
            self.states[LEFT] = True
        elif data[RIGHT]:
            self.servo.right()
            self.direction = RIGHT
            self.states[RIGHT] = True

    def __acc(self) -> None:
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
        self.direction = FORWARD
        self.left_wheel.stop()
        self.right_wheel.stop()
        self.current_speed = 0
