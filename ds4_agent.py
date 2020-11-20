from abc import ABC
from multiprocessing import Queue
from multiprocessing import Pipe
from pathlib import Path
from threading import Thread
from time import sleep

from agent_base import AgentBase
from subprocess import Popen, PIPE
from re import finditer
from multiprocessing import Process

from utils.constants import FORWARD
from json import dumps
from ps4 import MyController, read
from os import kill
from signal import SIGTERM


class DS4Agent(AgentBase):

    @staticmethod
    def poll(agent_queue: Queue):
        ds4_instance = DS4Agent()
        print("Creation of ds4_agent was successful")
        agent_queue.put(ds4_instance)
        sleep(5)

    def __init__(self):

        connected = False
        while not connected:
            mac_addr = None
            while not mac_addr:
                proc = Popen(args="hcitool scan", stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
                try:
                    stdout, stderr = proc.communicate(timeout=30)
                    matches_iterator = finditer(r'(\w{2}:){5}\w{2}', stdout)
                    while not mac_addr:
                        try:
                            matching_addr = next(matches_iterator)
                            device_name = stdout.split(matching_addr.group(0))[1].split('\n')[0].strip()
                            print(f'addr: {matching_addr.group(0)}, dev name: {device_name}')
                            if device_name == 'Wireless Controller':
                                mac_addr = matching_addr.group(0)
                        except StopIteration:
                            break
                except Exception as e: # TODO: handle timeout
                    print("no available devices")

            print('final addr: ', mac_addr)
            proc = Popen(args=f"sudo /home/alex/rc_controller_software/sh/connect {mac_addr}", stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)

            try:
                stdout, stderr = proc.communicate(timeout=30)
                print('stdout: ', stdout)
                print('stderr: ', stderr)
            except Exception as e:
                print("process not finished yet?", e)
            finally:
                proc.terminate()

            proc = Popen(args="hcitool con", stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
            try:
                stdout, stderr = proc.communicate(timeout=5)
                if mac_addr in stdout:
                    connected = True
                    # TODO: implement actual controller
                else:
                    print('not connected')

            finally:
                proc.terminate()

    def authenticate(self, password):
        return True  # TODO: implement authentication

    def receive(self) -> str:
        raise NotImplementedError

    def send(self, message: str) -> None:
        raise NotImplementedError

    def close_connection(self):
        """TODO: explain why is this function empty"""
        pass
