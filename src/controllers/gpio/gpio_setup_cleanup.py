from atexit import register

from RPi.GPIO import setmode, cleanup, BCM


setmode(BCM)
# TODO: gpiozero is included at the moment, which calls GPIO.cleanup, but when it will be removed, the next line should be uncommented
# register(cleanup)