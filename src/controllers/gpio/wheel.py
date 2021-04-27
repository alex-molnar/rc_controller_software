from controllers.gpio.output_device import GeneralPurposeOutputDevice


class Wheel:

    def __init__(self, forward_pin: int, backward_pin: int):
        self._forward_device = GeneralPurposeOutputDevice(forward_pin)
        self._backward_device = GeneralPurposeOutputDevice(backward_pin)

    def forward(self, speed: float = 1) -> None:
        self._backward_device.off()
        self._forward_device.on(speed)

    def backward(self, speed: float = 1) -> None:
        self._forward_device.off()
        self._backward_device.on(speed)

    def stop(self) -> None:
        self._forward_device.off()
        self._backward_device.off()
