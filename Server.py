import socket
from typing import Dict
import time
import Drone_data
class SERVER:
    def __init__(self, database : Drone_data.DRONE_DATA) -> None:
        self.drone_data : Dict =database.load_drone_state_chect_data()
        self.user_name : str =self.drone_data['user_name']
        self.drone_name : str =self.drone_data['drone_name']
        self.gcs_ip : str = socket.gethostbyname(socket.gethostname())
        self.gcs_port : int =self.drone_data['gcs_port']
        self.server_ip : str =self.drone_data['server_ip']
        self.server_port : int =self.drone_data['server_port']
    
    
    def get_ip(self) -> str:
        return self.gcs_ip
    
    
    def server_connect(self) -> bool:
        try:
            client_socket : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_ip, self.server_port))
            client_socket.sendall(('gcs').encode())
            time.sleep(0.1)
            client_socket.sendall(self.user_name.encode())
            time.sleep(0.1)
            client_socket.sendall(self.drone_name.encode())
            time.sleep(0.1)
            success : str =client_socket.recv(1024).decode()
            if success == 'success':
                client_socket.sendall(self.gcs_ip.encode())
                client_socket.sendall(str(self.gcs_port).encode())
                success : str =client_socket.recv(1024).decode()
                if success == 'success':
                    return True
                else:
                    print(success)
                    return False
            else:
                print(success)
                return False
        except:
            return False