from threading import Thread
from time import sleep
from collections import defaultdict

from gpiozero import Motor as Wheel

# TODO: refactor contained + distance keeping

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

    def __init__(self, right_wheel_pins, left_wheel_pins):
        self.right_wheel = Wheel(*right_wheel_pins)
        self.left_wheel = Wheel(*left_wheel_pins)

        self.state = STOP
        self.direction = FORWARD

        self.current_speed = 0

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

    def set_line(self, detected):
        self.line_detected = detected
        self.states[LINE] = detected

    def handle_motor_control(self, data):
        if data[DISTANCE_KEEPING]:
            if self.state == STOP:
                self.keeping_distance = True
                self.states[DISTANCE_KEEPING] = True
                Thread(target=self.__keep_distance).start()
        elif data[LINE_FOLLOWING]:
            if self.state == STOP:
                self.following_line = True
                self.states[LINE_FOLLOWING] = True
                Thread(target=self.__follow_line).start()
        elif data[KEEP_CONTAINED]:
            if self.state == STOP:
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
        else:
            self.__handle_speed(data)
            self.__handle_directions(data)

    def get_data(self):
        return self.states.items()

    def __keep_distance(self):
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

    def __follow_line(self):
        self.state = LINE_STATE
        while self.following_line:
            print(f"Following Line: {self.line_detected}")
            sleep(0.5)
        print('Not Following Line Anymore..')
        self.__stop()

    def __keep_contained(self):
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

    def __handle_speed(self, data):
        if self.direction == FORWARD:
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

    def __handle_directions(self, data):
        if self.state in [STOP, DISTANCE_STATE, LINE_STATE]:
            if self.direction == FORWARD:
                if data[RIGHT]:
                    self.states[RIGHT] = True
                    self.__turn(right=True)
                elif data[LEFT]:
                    self.states[LEFT] = True
                    self.__turn(right=False)
            elif self.direction == RIGHT:
                if not data[RIGHT]:
                    self.states[RIGHT] = False
                    if data[LEFT]:
                        self.states[LEFT] = True
                        self.__turn(right=False)
                    else:
                        self.__stop()
            elif self.direction == LEFT:
                if not data[LEFT]:
                    self.states[LEFT] = False
                    if data[RIGHT]:
                        self.states[RIGHT] = True
                        self.__turn(right=True)
                    else:
                        self.__stop()

    def __acc(self):
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

    def __break(self):
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

    def __turn(self, right):
        self.direction = RIGHT if right else LEFT
        if right:
            self.left_wheel.forward(self.TURN_FORWARD_SPEED)
            self.right_wheel.backward(self.TURN_BACKWARD_SPEED)
        else:
            self.right_wheel.forward(self.TURN_FORWARD_SPEED)
            self.left_wheel.backward(self.TURN_BACKWARD_SPEED)

    def __stop(self):
        self.state = STOP
        self.direction = FORWARD
        self.left_wheel.stop()
        self.right_wheel.stop()
        self.current_speed = 0
