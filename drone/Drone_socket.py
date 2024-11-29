import socket
from typing import Dict, List
import cv2
import numpy as np
import time
import pickle
import queue
import threading

class DRONE_SOCKET:
    def __init__(self, drone_init_data : Dict, gcs_ip : str, gcs_port : int) -> None:
        self.drone_init_data : Dict = drone_init_data
        self.gcs_ip : str = gcs_ip
        self.gcs_port : int = gcs_port
        self.drone_environment : int =  self.drone_init_data['drone_environment']
        self.connect : bool = False
        self.socket_list : List[socket.socket]
        self.command_que : queue.Queue = queue.Queue(maxsize=3)
        self.error : queue.Queue = queue.Queue(maxsize=3)
        self.cancle : threading.Event = threading.Event()
        self.lock = threading.Lock()
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
        
    
    def connect_cancle(self) -> None:
        self.cancle.wait()
        for s in self.socket_list:
            s.close()
        self.cancle.clear()
        
        
    def connect_cancle_command(self) -> None:
        self.cancle.set()  
         
        
    def command_streaming(self, command_socket : socket.socket) -> None:
        try:
            while 1:
                message_byte : bytes = command_socket.recv(1024)
                command_message : Dict = pickle.loads(message_byte)
                try:
                    self.command_que.put(command_message, block=False)
                except queue.Full:
                    self.command_que.get_nowait()
                    self.command_que.put(command_message)
        except Exception as e:
            self.error.put(str(e))
            print(str(e))
            command_socket.close()
            return
        
    
    def get_command(self) -> Dict:
        command_message : Dict =self.command_que.get()
        return command_message
    
                
    def video_streaming(self, video_socket : socket.socket) -> None:
        
        try:
            if self.drone_environment:
                import video
                video_virtual : video.Video = video.Video()
                while 1:
                    if not video_virtual.frame_available():
                        continue
                    frame : np.ndarray = video_virtual.frame()
                    frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR) 
                    frame_byte : bytes = pickle.dumps(frame)
                    frame_size : int = len(frame_byte)
                    video_socket.sendall(frame_size.to_bytes(4, byteorder='big'))           
                    video_socket.sendall(frame_byte)
            else:
                video_real: cv2.VideoCapture = cv2.VideoCapture(0)
                success : bool
                frame : np.ndarray
                while 1:
                    success, frame = video_real.read()
                    if success:
                        frame = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_LINEAR)
                        frame_byte : bytes = pickle.dumps(frame)
                        frame_size : int = len(frame_byte)
                        video_socket.sendall(frame_size.to_bytes(4, byteorder='big'))           
                        video_socket.sendall(frame_byte)
        except Exception as e:
            self.error.put(str(e))
            print(str(e))
            video_socket.close()
            return
             
    
    def state_streaming(self, state_socket : socket.socket) -> None:
        try:
            while 1:
                data = pickle.dumps(self.state)
                state_socket.sendall(data)
                time.sleep(0.1)
        except Exception as e:
            self.error.put(str(e))
            print(str(e))
            state_socket.close()
            return
    
    
    def drone_socket_main(self) -> str:
        try:
            connect_cancle_thread : threading.Thread = threading.Thread(target=self.connect_cancle)
            connect_cancle_thread.daemon=True
            connect_cancle_thread.start()
            
            connect_list : List[str] = ['vid','state','command']
            thread_list : List[threading.Thread] = []
            for client in connect_list:
                try:
                    client_socket : socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((self.gcs_ip, self.gcs_port))
                    client_socket.sendall((client).encode())
                    time.sleep(0.1)
                    if client =='vid':
                        vid_thread : threading.Thread = threading.Thread(target=self.video_streaming, args=(client_socket,))
                        vid_thread.daemon=True
                        thread_list.append(vid_thread)
                        vid_thread.start()
                    if client =='state':
                        state_thread : threading.Thread = threading.Thread(target=self.state_streaming, args=(client_socket,))
                        state_thread.daemon=True
                        thread_list.append(state_thread)
                        state_thread.start()
                    if client =='command':
                        command_thread : threading.Thread = threading.Thread(target=self.command_streaming, args=(client_socket,))
                        command_thread.daemon=True
                        thread_list.append(command_thread)
                        command_thread.start()
                except Exception as e:
                    return client+' fail '+str(e)
            self.connect = True
            return 'end'
        except Exception as e:
            return str(e)
        
            