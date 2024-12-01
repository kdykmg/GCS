from typing import Dict, List
import Drone_init_data
import Drone_sever_connecter
import Drone_socket
import Drone_object
import Drone_command_data_get
import asyncio
import Drone_state_get


class DRONE_MAIN:
    def __init__(self) -> None:
        self.Drone_init_data :Drone_init_data.DRONE_INIT_DATA = Drone_init_data.DRONE_INIT_DATA()
        self.drone_init_data : Dict =self.Drone_init_data.load_drone_init_data()
        self.Drone_server_connect : Drone_sever_connecter.DRONE_SERVER_CONNECTER = Drone_sever_connecter.DRONE_SERVER_CONNECTER(self.drone_init_data)
        self.connect_waiting_time : int = 10
        
    async def main(self) -> None:
        connect : bool = False
        for i in range(int(self.connect_waiting_time/5)):
            result : List = self.Drone_server_connect.connect_server()
            if result[0] == 'success':
                gcs_ip : str = result[1]
                gcs_port : int = int(result[2])
                connect = True
                break
            print(f'try {i+1} time connect false')
            await asyncio.sleep(5)
        if not connect:
            return
        drone_socket : Drone_socket.DRONE_SOCKET = Drone_socket.DRONE_SOCKET(self.drone_init_data, gcs_ip, gcs_port)
        drone_state_streamer : Drone_state_get.DRONE_STATE_GET = Drone_state_get.DRONE_STATE_GET(drone_socket)
        for i in range(int(self.connect_waiting_time/5)):
            try :
                result_socket : str = drone_socket.drone_socket_main()
                if result_socket == 'end':
                    i = 0
                    drone_command_data_get : Drone_command_data_get.DRONE_COMMAND_DATA_GET = Drone_command_data_get.DRONE_COMMAND_DATA_GET(drone_socket)
                    drone_command : Drone_object.DRONE_OBJECT = Drone_object.DRONE_OBJECT(drone_command_data_get, drone_state_streamer, drone_socket) 
                    await drone_command.command_main()
                    drone_socket.connect_cancle_command()
                    return
                else :
                    print(result_socket)
                    await asyncio.sleep(5)
            except Exception as e:
                print(str(e))
                await asyncio.sleep(5)
            
            
if __name__ == "__main__":
    drone_main_instance = DRONE_MAIN()
    asyncio.run(drone_main_instance.main())
    exit()
    