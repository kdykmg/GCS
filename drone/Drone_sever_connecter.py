import socket
from typing import Dict
import time
import Drone_init_data

class DRONE_SERVER_CONNECTER:
    def __init__(self,drone_init_data : Dict) -> None:
        self.drone_init_data : Dict = drone_init_data
        self.user_name : str = self.drone_init_data['user_name']
        self.drone_name : str = self.drone_init_data['drone_name']
        self.server_ip : str = self.drone_init_data['server_ip']
        self.server_port : int = self.drone_init_data['server_port']
        
        
    def connect_server(self) -> list:
        try:
            client_socket : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_ip, self.server_port))
            client_socket.sendall(('drone').encode())
            time.sleep(0.1)
            client_socket.sendall(self.user_name.encode())
            time.sleep(0.1)
            client_socket.sendall(self.drone_name.encode())
            success : str = client_socket.recv(1024).decode()
            print(success)
            if success == 'success':
                result = ['success']
                gcs_ip : str = client_socket.recv(1024).decode()
                print(gcs_ip)
                result.append(gcs_ip)
                gcs_port : str = client_socket.recv(1024).decode()
                print(gcs_port)
                result.append(gcs_port)
                return result
            else:
                return[success]
        except Exception as e:
            return[e]