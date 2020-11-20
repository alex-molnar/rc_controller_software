from abc import ABC, ABCMeta
from queue import Queue


class AgentBase(ABC, metaclass=ABCMeta):

    @staticmethod
    def poll(agent_queue: Queue):
        raise NotImplementedError

    def authenticate(self, password):
        raise NotImplementedError

    def receive(self) -> str:
        raise NotImplementedError
    
    def send(self, message: str) -> None:
        raise NotImplementedError

    def close_connection(self):
        raise NotImplementedError
