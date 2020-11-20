from multiprocessing import Process, Queue
from json import dumps, loads
from threading import Thread

from controller import Controller
from lan_agent import LAN_Agent
from bluetooth_agent import BluetoothAgent
from ds4_agent import DS4Agent
from agent_base import AgentBase
from hashlib import sha256
from utils.constants import SUCCESS, AUTHENTICATION_FAILURE, AGENT_CONNECTED

from sys import argv
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
        self.agent: AgentBase = None
        self.agent_queue: "Queue[AgentBase]" = Queue()
        self.poll_processes = dict()

        password = "69420"  # TODO: get password from file
        self.password = sha256(password.encode()).digest()

        # self.poll_processes[str(LAN_Agent)] = Process(target=LAN_Agent.poll, args=(self.agent_queue,))
        self.poll_processes[str(DS4Agent)] = Process(target=DS4Agent.poll, args=(self.agent_queue,))
        # self.poll_processes[str(LAN_Agent)].start()
        self.poll_processes[str(DS4Agent)].start()

        while not self.agent:
            print('before get')
            candidate_agent = self.agent_queue.get()
            print('after get')
            if candidate_agent.authenticate(self.password):
                self.agent = candidate_agent
                self.controller = Controller()
                self.is_connection_alive = True
                for process in self.poll_processes.values():
                    process.terminate()
            else:
                candidate_agent.close_connection()
                self.poll_processes[str(candidate_agent)] = Process(target=type(candidate_agent).poll, args=(self.agent_queue,))
                self.poll_processes[str(candidate_agent)].start()

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
            data = self.agent.receive()
            if not data:
                self.is_connection_alive = False
                break
            else:
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
    if len(argv) > 1 and argv[1] == '--debug':
        b = DS4Agent()
    else:
        RC_Car().run()
