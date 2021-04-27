from atexit import register

from RPi.GPIO import setmode, cleanup, BCM


setmode(BCM)
register(cleanup)
