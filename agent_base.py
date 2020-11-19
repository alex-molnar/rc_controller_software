from abc import ABC

class AgentBase(ABC):
    def receive(self) -> str:
        pass
    
    def send(self, message: str) -> None:
        pass

    def receive_passwd(self) -> str:
        pass

    def send_passwd(self) -> None:
        pass

    def close_connection(self):
        pass
