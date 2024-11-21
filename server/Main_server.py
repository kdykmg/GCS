import socket
import threading
from typing import Dict, List, Tuple
import json
import os
import time
path=os.path.dirname(__file__)
path=path+''
os.chdir(path)

class MAIN_SERVER:
    def __init__(self) -> None:
        import socket
        self.server_ip : str = socket.gethostbyname(socket.gethostname())
        self.server_port : int = 5555
        self.user_drone : Dict[str,List] = dict()
        self.user_net : Dict[str,List] = dict()
        self.server_socket : socket.socket
        self.load_user_drone_data()
        
        
    def load_user_drone_data(self) -> None:
        with open('user_drone_data.json','r') as f:
            loaded_data : Dict= json.load(f)
            for key, value in loaded_data.items():
                self.user_drone[key] = value
   
   
    def save_user_drone_data(self) -> None:
        with open('user_drone_data.json','w') as f:
            json.dump(self.user_drone,f)
    
           
    def edit_user_data(self) -> None:
        try:
            print('==========')
            for key, value in self.user_drone.items():
                print(f"user: {key} drone:{value}")
            print('==========')
            user_name : str = input('user name >>')
            for key, value in self.user_drone.items():
                if key == user_name:
                    while 1:
                        try:
                            command : int = int(input('1 : change name\n2 : delete drone\n3 : delete user\n4 : exit\n'))
                            if command == 1:
                                new_name : str = input('change name >>')
                                for name, value in self.user_drone.items():
                                    if name == new_name:
                                        print('already exists')
                                        continue
                                self.user_drone[new_name] = self.user_drone.pop(key)
                                key=new_name
                                print('sucess')
                            if command == 2:
                                drone_name : str = input('drone name >>')
                                try:
                                    self.user_drone[key].remove(drone_name)
                                    print('success')
                                except :
                                    print('fail')
                                    continue
                            if command == 3:
                                delete_name : str = input('drone name >>')
                                try:
                                    self.user_drone.pop(delete_name)
                                    print('success')
                                except :
                                    print('fail')
                                    continue
                            if command == 4:
                                return
                        except ValueError:
                            continue
                        except Exception as e:
                            print(str(e))
            print('not exists')
        except Exception as e:
            print(str(e))   
            return
        
               
    def add_user(self) ->None :
        try:
            user_name : str = input('user name >>')
            for key, value in self.user_drone.items():
                if key == user_name:
                    print('already exists')
                    return
            self.user_drone[user_name] =[]
            self.save_user_drone_data()
            print('success')
            return
        except Exception as e:
            print(str(e))
            return
    
    
    def add_drone(self) -> None:
        try:
            check_exists : bool = False
            user_name : str = input('user name >>')
            for key, value in self.user_drone.items():
                if user_name == key:
                    check_exists =True
                    break
            if check_exists :
                drone_name : str = input('drone name >>')
                for key, value in self.user_drone.items():
                    if drone_name in value:
                        print('already exists')
                        return
                self.user_drone[user_name].append(drone_name)
                self.save_user_drone_data()
                print('success')
                return
            else:
                print('not exists')
                return
        except Exception as e:
            print(str(e))
            return
		

    def waiting_user(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.server_ip, self.server_port))
        self.server_socket.listen(10)
        try:
            while 1 :
                client_socket : socket.socket
                address : Tuple[str, int]
                client_socket, address = self.server_socket.accept()
                part : str = client_socket.recv(1024).decode()
                if part == 'gcs':
                    user_name : str = client_socket.recv(1024).decode()
                    drone_name : str = client_socket.recv(1024).decode()
                    success : str = 'fail'
                    if user_name and drone_name != None:
                        try :
                            drone_list : List[str] = self.user_drone[user_name]
                            
                            if drone_name in drone_list:
                                success = 'success'
                            else:
                                success = 'no drone name'
                        except :
                            success = 'no user name'
                            client_socket.sendall(success.encode())
                            continue
                    client_socket.sendall(success.encode())
                    if success == 'success':
                        success = 'fail'
                        try:
                            gcs_ip : str = client_socket.recv(1024).decode()
                            gcs_port : str = client_socket.recv(1024).decode()
                            self.user_net[user_name] = [drone_name, gcs_ip, gcs_port]
                            success = 'success'
                            client_socket.sendall(success.encode())
                        except :
                            client_socket.sendall(('fail').encode())
                            continue
                if part == 'drone':
                    print(self.user_net)
                    user_name : str = client_socket.recv(1024).decode()
                    drone_name : str = client_socket.recv(1024).decode()
                    success : str = 'fail'
                    if user_name and drone_name != None:
                        try :
                            if self.user_net[user_name][0] == drone_name:
                                gcs_ip : str = self.user_net[user_name][1]
                                gcs_port : str = self.user_net[user_name][2]
                                success = 'success'
                            else : 
                                success = 'no drone name'
                        except :
                            success = 'no user name'
                            client_socket.sendall(success.encode())
                            continue
                    client_socket.sendall(success.encode())
                    time.sleep(0.1)
                    if success == 'success':
                        client_socket.sendall(gcs_ip.encode())
                        time.sleep(0.1)
                        client_socket.sendall(gcs_port.encode())
        except Exception as e:
            self.server_socket.close()
            print(str(e))
            return
                          
                        
    def server_main(self) -> None:
        user_connect_threading : threading.Thread = threading.Thread(target=self.waiting_user)
        user_connect_threading.daemon=True
        user_connect_threading.start()
        while 1:
            try:
                command : int = int(input('1 : add user\n2 : add drone\n3 : edit user\n4 : exit\n'))
                if command == 1:
                    self.add_user()
                if command == 2:
                    self.add_drone()
                if command == 3:
                    self.edit_user_data()
                if command == 4:
                    exit()
            except ValueError:
                continue
            except Exception as e:
                print(str(e))
                exit()
                
                
d=MAIN_SERVER()
d.server_main()