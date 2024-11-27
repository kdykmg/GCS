from typing import Dict
import Socket

class COMMAND:
    def __init__(self, command_socket : Socket.SOCKET, drone_key_data : Dict) -> None:
        self.command_socket : Socket.SOCKET = command_socket
        self.key_state_before : Dict[str, bool] = drone_key_data
        

    def command_to_socket(self, key_state : Dict[str, bool]) -> None:
        command : Dict[str, bool] =dict()
        for key, value in key_state.items():
            if value != self.key_state_before[key]:
                if key == 'arm' or key == 'takeoff' or key == 'land' or key == 'disarm' or key == 'comeback':
                    if value :
                        command[key] = value
                else:
                    command[key] = value
                self.key_state_before[key] = value
        if len(command) != 0:
            self.command_socket.send_command(command)
            