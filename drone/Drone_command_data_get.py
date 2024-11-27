import Drone_socket
from typing import Dict


class DRONE_COMMAND_DATA_GET:
    def __init__(self, drone_socket : Drone_socket.DRONE_SOCKET) -> None:
        self.drone_socket = drone_socket
        
    
    def get_command(self) -> Dict:
        command : Dict = self.drone_socket.get_command()
        return command