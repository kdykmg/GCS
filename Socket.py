from typing import Tuple, Dict, List
import socket
import pickle
import numpy as np
import threading
import queue

class SOCKET:
    def __init__(self, user_name : str, drone_name : str, gcs_port : int) -> None:
        self.user_name : str = user_name
        self.drone_name : str = drone_name
        self.gcs_ip : str
        self.gcs_port : int = gcs_port
        self.connect : bool = False
        self.gcs_socket : socket.socket
        self.state : Dict = dict(
            video=0.0,
            speed=0.0,
            location_latitude=37.5665,
            location_longitude=126.9780,
            altitude=0.0,
            battery=0.0,
            yaw=0.0,
            pitch=0.0,
            roll=0.0,
            msg=''
        )
        self.cancle : threading.Event = threading.Event()
        self.lastet_frame : np.ndarray = np.zeros((360, 640, 3), np.uint8)
        self.command_que : queue.Queue[bytes] = queue.Queue(maxsize=3)
        self.error : queue.Queue = queue.Queue(maxsize=3)
        self.lock = threading.Lock() 
        
 
    def creat_socket(self) -> None:
        self.gcs_ip : str = socket.gethostbyname(socket.gethostname())
        self.gcs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gcs_socket.bind((self.gcs_ip, self.gcs_port))
        self.gcs_socket.listen(10)
        

    def connect_cancle(self) -> None:
        self.cancle.wait()
        self.gcs_socket.close()
        self.cancle.clear()
        
        
    def connect_cancle_command(self) -> None:
        self.cancle.set()
        
 
    def vid_streaming(self, video_socket : socket.socket, address: Tuple[str, int]) -> None:
        try:
            while 1:
                frame_size_bytes : bytes = video_socket.recv(4)
                frame_size : int = int.from_bytes(frame_size_bytes, byteorder='big')
                if frame_size==0:
                    continue
                frame_data : bytes = b''
                while len(frame_data) < frame_size:
                    packet : bytes = video_socket.recv(frame_size - len(frame_data))
                    if not packet:
                        break
                    frame_data += packet
                frame : np.ndarray = pickle.loads(frame_data)
                with self.lock:
                    self.lastet_frame=frame
        except Exception as e:
            self.error.put(str(e))
            video_socket.close()
            return
        

    def get_vid(self) -> np.ndarray:
        frame : np.ndarray = self.lastet_frame
        return frame
    
    
    def state_streaming(self, state_socket : socket.socket, address : Tuple[str, int]) -> None:
        state_message : Dict
        try:
            while 1:
                state_message = pickle.loads(state_socket.recv(1024))
                if state_message != None:
                    with self.lock:
                        for key, value in state_message.items():
                            self.state[key]=value
        except Exception as e:
            self.error.put(str(e))
            state_socket.close()
            return


    def command_streaming(self, command_socket : socket.socket, address : Tuple[str, int]) -> None:
        try:
            while 1:
                command_message : bytes =self.command_que.get()
                command_socket.sendall(command_message)
        except Exception as e:
            self.error.put(str(e))
            command_socket.close()
            return
        
        
    def send_command(self, command : Dict[str,bool]) -> None:
        command_message : bytes = pickle.dumps(command)
        try:
            self.command_que.put(command_message, block=False)
        except queue.Full:
            self.command_que.get_nowait()
            self.command_que.put(command_message)
    
    
    def connect_drone(self) -> str:
        try:
            print('opening socket...')
            
            self.gcs_ip : str = socket.gethostbyname(socket.gethostname())
            
            self.gcs_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.gcs_socket.bind((self.gcs_ip, self.gcs_port))
            self.gcs_socket.listen(10)
            self.creat_socket()
            connect : bool = True
            connect_cancle_thread : threading.Thread = threading.Thread(target=self.connect_cancle)
            connect_cancle_thread.daemon=True
            connect_cancle_thread.start()
            thread_list : List[threading.Thread] = []
            connect_list : Dict[str, bool] = dict(
                vid_connect=False,
                state_connect=False,
                command_connect=False
            )
            while 1:
                connect = False
                client_socket : socket.socket
                address : Tuple[str, int]
                for _, value in connect_list.items():
                    if not value:
                        connect = True
                if connect:
                    client_socket, address = self.gcs_socket.accept()
                    part : str = client_socket.recv(1024).decode()
                    if part == 'vid':
                        vid_thread : threading.Thread = threading.Thread(target=self.vid_streaming, args=(client_socket, address))
                        vid_thread.daemon=True
                        thread_list.append(vid_thread)
                        connect_list['vid_connect']=True
                        vid_thread.start()
                    if part == 'state':
                        state_thread : threading.Thread = threading.Thread(target=self.state_streaming, args=(client_socket, address))
                        state_thread.daemon=True
                        thread_list.append(state_thread)
                        connect_list['state_connect']=True
                        state_thread.start()
                    if part == 'command':
                        command_thread : threading.Thread = threading.Thread(target=self.command_streaming, args=(client_socket, address))
                        command_thread.daemon=True
                        thread_list.append(command_thread)
                        connect_list['command_connect']=True
                        command_thread.start()
                else:
                    break
            self.connect = True
            return 'end'
        except Exception as e:
            print(str(e))
            return str(e)
        