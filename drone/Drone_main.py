import socket
from typing import Dict, List
import time
import Drone_init_data
import Drone_sever_connecter
import Drone_socket
#import Drone_object
import Drone_command_data_get
import asyncio


class DRONE_MAIN:
    def __init__(self) -> None:
        self.Drone_init_data :Drone_init_data.DRONE_INIT_DATA = Drone_init_data.DRONE_INIT_DATA()
        self.drone_init_data : Dict =self.Drone_init_data.load_drone_init_data()
        self.Drone_server_connect : Drone_sever_connecter.DRONE_SERVER_CONNECTER = Drone_sever_connecter.DRONE_SERVER_CONNECTER(self.drone_init_data)
        
        
    async def main(self) -> None:
        result : List = self.Drone_server_connect.connect_server()
        print(result)
        if result[0] == 'success':
            gcs_ip : str = result[1]
            gcs_port : int = int(result[2])
            
        else :
            print(result[0])
            exit()
        drone_socket : Drone_socket.DRONE_SOCKET = Drone_socket.DRONE_SOCKET(self.drone_init_data, gcs_ip, gcs_port)
        result_socket : str = drone_socket.drone_socket_main()
        if result_socket == 'end':
            drone_command_data_get : Drone_command_data_get.DRONE_COMMAND_DATA_GET = Drone_command_data_get.DRONE_COMMAND_DATA_GET(drone_socket)
            #drone_command : Drone_object.DRONE_OBJECT = Drone_object.DRONE_OBJECT(drone_command_data_get) 
            #await drone_command.command_main()
            while 1:
                msg : Dict = drone_command_data_get.get_command()
                for i , j in msg.items():
                    print(i,j)
                    if i == 'end':
                        exit()
        else :
            print(result_socket)
            return
            
if __name__ == "__main__":

    drone_main_instance = DRONE_MAIN()
    asyncio.run(drone_main_instance.main())

    