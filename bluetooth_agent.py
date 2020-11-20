from agent_base import AgentBase


class BluetoothAgent(AgentBase):

    def __init__(self):
        print('not yet')

    def receive(self) -> str:
        raise NotImplementedError

    def send(self, message: str) -> None:
        raise NotImplementedError

    def receive_password(self) -> str:
        raise NotImplementedError

    def send_password(self) -> None:
        raise NotImplementedError

    def close_connection(self):
        raise NotImplementedError