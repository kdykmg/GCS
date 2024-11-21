from typing import Dict
import Socket
import Gui
import Command
import time
import Drone_data
import Server
import Map
import msvcrt
import sys
import Drone_state

class MAIN:
    def __init__(self) -> None:
        self.drone_data :Drone_data.DRONE_DATA = Drone_data.DRONE_DATA()
        self.drone_init_data : Dict = self.drone_data.load_drone_state_chect_data()
        self.drone_key_data : Dict = self.drone_data.load_drone_command_key_data()
        self.user_name : str = self.drone_init_data['user_name']
        self.drone_name : str = self.drone_init_data['drone_name']
        self.gcs_port : str = str(self.drone_init_data['gcs_port'])
        self.server : Server.SERVER = Server.SERVER(self.drone_data)

        
    def input_data(self, prompt : str, default : str) -> str:
        print(prompt, end='', flush=True)
        sys.stdout.write(default)
        sys.stdout.flush()
        
        result : str = default
        while True:
            key = msvcrt.getch()
            if key == b'\r':
                print()
                return result
            elif key == b'\x08':
                if len(result) > 0:
                    result = result[:-1]
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif key == b'\xe0':
                msvcrt.getch()
            elif 32 <= ord(key) <= 126:
                result += key.decode('ascii')
                sys.stdout.write(key.decode('ascii'))
                sys.stdout.flush()
            
            
    def main(self) -> None:
        drone_data : Drone_data.DRONE_DATA =Drone_data.DRONE_DATA()
        user_name : str = self.input_data('user_name :',self.user_name)
        drone_data.save_data({'user_name':user_name})
        drone_name : str = self.input_data('drone_name :',self.drone_name)
        drone_data.save_data({'drone_name':drone_name})
        gcs_port : int = int(self.input_data('gcs_port :',self.gcs_port))
        drone_data.save_data({'gcs_port':gcs_port})
        server : Server.SERVER =Server.SERVER(drone_data)
        print('connecting server ...')
        while 1:
            result : bool = server.server_connect()
            if result:
                break
            else:
                time.sleep(1)
                return
        drone_socket : Socket.SOCKET =Socket.SOCKET(user_name, drone_name, gcs_port)
        drone_socket.connect_drone()
        command_to_socket_def : Command.COMMAND = Command.COMMAND(drone_socket, self.drone_key_data)
        Drone_state_stream : Drone_state.DRONE_STATE = Drone_state.DRONE_STATE(drone_socket)
        Drone_map_stream : Map.MAP = Map.MAP(Drone_state_stream)

        gcs_gui : Gui.GUI = Gui.GUI(drone_socket, drone_data, command_to_socket_def, Drone_state_stream,Drone_map_stream)
        return_code : str = gcs_gui.gui_main()
        if return_code =='end':
            drone_socket.connect_cancle_command()
            
            
mai=MAIN()

mai.main()
exit()