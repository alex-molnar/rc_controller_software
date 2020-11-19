from threading import Thread, Lock
from json import dumps, loads
from controller import Controller
from lan_agent import LAN_Agent
from agent_base import AgentBase
from hashlib import sha256
from queue import Queue
from utils.constants import SUCCESS, AUTHENTICATION_FAILURE, AGENT_CONNECTED

from time import sleep

class RC_Car:
    """
    The entrypoint of the software for the RC car created like this: TODO: link
    By default it will listen on an available port in a range 8000, 60000

    :examples:

    >>> car = RC_Car()
    >>> car.run()
    """
    def __init__(self):
        """
        Creates the instance of the RC_Car class. 
          * Starts to listen, on a free port in range 8000, 60000,
          * If a connection request received it establishes the connection with the client. 
          * Creates the instance of the controller class

        :Assumptions:
          * Only one instance of the class is created
        """
        self.agent = None
        self.agent_queue = Queue()
        self.authenticating = False
        self.is_connection_alive = True
        password = "69420" #TODO: get passwd from file
        self.password = sha256(password.encode()).digest()

        Thread(target=LAN_Agent.get_instance, args=(self,)).start()
        print('before get')
        self.agent_queue.get()
        print('after get')

    def __authenticate(self) -> bool:
        self.authenticating = True
        success = AUTHENTICATION_FAILURE
        if self.agent is not None:
            data = self.agent.receive_passwd() #receiving_socket.recv(1024)
            print(f'data: {data} vs\npasswd: {self.password}')
            if data == self.password:
                print('  ...GRANTED.')
                self.agent.send_passwd() #sending_socket.sendall(b"GRANTED\n")
                print('sent')
                self.controller = Controller()
                self.agent_queue.put(True)
                success = SUCCESS

        self.authenticating = False
        return success

    def set_agent(self, agent: AgentBase) -> bool:
        """"""
        if self.agent is None:
            self.agent = agent
            return self.__authenticate()
        elif self.authenticating:
            sleep(1)
            return self.set_agent(agent)
        else:
            return AGENT_CONNECTED

    def run(self) -> None:
        """
          * Starts the thread which sends updates on the state of the controller
          * Starts the method which is responsible for receiving the commands from the client.

          Note: It blocks until the the client ends connection.

          :return: None
        """
        update_thread = Thread(target=self.send_updates)
        update_thread.start()
        self.receive_commands()
        update_thread.join()
        
    def receive_commands(self) -> None:
        """
        Listens on the receiving socket in an infinite loop.

        :Assumpitons: None

        :return: None
        """
        while True:
            data = self.agent.receive() #.receiving_socket.recv(1024).decode()
            if not data:
                self.is_connection_alive = False
                break
            else:
                print('setting values')
                self.controller.set_values(loads(data))

    def send_updates(self) -> None:
        """
        Constantly update the client about the state of the controller
        
        :Assumpitons: None

        :return: None
        """
        while self.is_connection_alive:
            message = dumps(self.controller.get_values()) + '\n'
            self.agent.send(message)
            sleep(0.05) # distance sensor


if __name__ == '__main__':
    RC_Car().run()
