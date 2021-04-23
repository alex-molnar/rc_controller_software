from controllers.gpio.output_device import GeneralPurposeOutputDevice


class Wheel:

    def __init__(self, forward_pin, backward_pin):
        self._forward_device = GeneralPurposeOutputDevice(forward_pin)
        self._backward_device = GeneralPurposeOutputDevice(backward_pin)

    def forward(self, speed=1):
        self._backward_device.off()
        self._forward_device.value = speed

    def backward(self, speed=1):
        self._forward_device.off()
        self._backward_device.value = speed

    def stop(self):
        self._forward_device.off()
        self._backward_device.off()
