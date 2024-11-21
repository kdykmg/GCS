import numpy as np
import cv2
import cvui
from typing import Dict, List
import Drone_data
import Map
import keyboard
import Command
import threading
import Drone_state
import Socket


class GUI:
    def __init__(self, vid_streaming : Socket.SOCKET, database : Drone_data.DRONE_DATA, command_data : Command.COMMAND , drone_state_streaming : Drone_state.DRONE_STATE, drone_map : Map.MAP) -> None:
        self.WINDOW_NAME : str = 'gui_test'
        self.drone_data : Drone_data.DRONE_DATA = database
        self.command_data : Command.COMMAND = command_data
        self.state_data : Drone_state.DRONE_STATE = drone_state_streaming
        self.vid_streaming : Socket.SOCKET = vid_streaming
        self.drone_map : Map.MAP = drone_map
        self.not_show_img : np.ndarray = np.zeros((360, 640, 3), np.uint8)
        self.frame : np.ndarray = np.zeros((720, 1280, 3), np.uint8)
        self.frame[:] = (49, 52, 49)
        self.frameRows: int = self.frame.shape[0]
        self.frameCols: int = self.frame.shape[1]
        self.auto_state : bool = True
        self.lock = threading.Lock() 
        self.key_state : Dict[str, bool] = self.drone_data.load_drone_command_key_data()
        self.drone_state : Dict[str, float] = dict(
            video=0.0,
            speed=0.0,
            location_latitude=0.0,
            location_longitude=0.0,
            altitude=0.0,
            battery=0.0,
            yaw=0.0,
            pitch=0.0,
            roll=0.0
        )
        self.drone_state_chect : Dict[str, List[bool]] ={}
        self.drone_state_chect_data : Dict = self.drone_data.load_drone_state_chect_data()
        for key in self.drone_state.keys():
            self.drone_state_chect[key] = self.drone_state_chect_data[key]
        self.check_box_start_point : List[int] =[1050,30]
        self.show_box_start_point : List[int] =[640,410]
        self.check_box_gap : int = 0
        self.show_box_gap : List[int] = [0,0]
        self.drone_state_chect_box_locate : Dict[str, List[int]] = {}
        for key in self.drone_state.keys():
            self.drone_state_chect_box_locate[key] = [self.check_box_start_point[0],self.check_box_start_point[1]+self.check_box_gap]
            self.check_box_gap+=30
        self.drone_state_showbox_locate : Dict[str, List[int]] = {}
        for key in self.drone_state.keys():
            if key== 'video':
                continue
            self.drone_state_showbox_locate[key] = [self.show_box_start_point[0]+self.show_box_gap[0],self.show_box_start_point[1]+self.show_box_gap[1]]
            if self.frameCols-self.show_box_start_point[0]-self.show_box_gap[0]-300>0:
                self.show_box_gap[0] += 140
            else:
                self.show_box_gap[0]=0
                self.show_box_gap[1]+=90
            
        self.drone_state_chectbox_show : bool = False
        self.drone_state_data_show : bool = False
        
        
    def save_data(self) -> None:
        self.drone_data.save_data(self.drone_state_chect)
        if self.auto_state:
            threading.Timer(1, self.save_data).start()
        else: 
            return
    
    
    def update_drone_state(self) -> None:
        latest_drone_state_data: Dict[str,float] = self.state_data.get_drone_info_streaming()
        with self.lock:
            for key, value in self.drone_state_chect.items():
                if value[0]:
                    self.drone_state[key] = latest_drone_state_data[key]
                else:
                    self.drone_state[key] = 0.0
        if self.auto_state:
            threading.Timer(0.1, self.update_drone_state).start()
            
                
    def put_action(self, key : str) -> None:
        self.key_state[key]=True

            
    def release_all_key(self) -> None:
        for key in self.key_state.keys():
            self.key_state[key]=False
            
            
    def gui_main(self) -> str:
        cvui.init(self.WINDOW_NAME)
        self.save_data()
        self.update_drone_state()
        while True:
            self.release_all_key()
            self.frame[:] = (204, 204, 204)
            if self.drone_state_chect['video'][0]:
                img : np.ndarray = self.vid_streaming.get_vid()
            else :
                img : np.ndarray = self.not_show_img
            if cvui.button(self.frame, 10, 10, img, img, img):
                pass
            cvui.rect(self.frame, 8, 8, 642, 362, 0x000000)
            map_img=self.drone_map.get_map()
            if cvui.button(self.frame, 660, 10, map_img, map_img, map_img):
                pass
            if cvui.button(self.frame, 1050, 10, 200, 20, ''):
                if self.drone_state_chectbox_show:
                    self.drone_state_chectbox_show = False
                else:
                    self.drone_state_chectbox_show = True
            if self.drone_state_chectbox_show:
                cvui.window(self.frame, 1050, 10, 200, 300, 'Information to Display')
                for key, value in self.drone_state_chect.items():
                    cvui.checkbox(self.frame, self.drone_state_chect_box_locate[key][0],self.drone_state_chect_box_locate[key][1], key, value, 0xffffff)
            else:
                cvui.window(self.frame, 1050, 10, 200, 20, 'Information to Display')
            cvui.rect(self.frame, 4, 400, self.frameCols-8, 314, 0x000000, 0x999999)
            for key, value in self.drone_state.items():
                if key =='video': continue
                cvui.window(self.frame,self.drone_state_showbox_locate[key][0],self.drone_state_showbox_locate[key][1],120,80,key)
                cvui.text(self.frame,self.drone_state_showbox_locate[key][0]+30,self.drone_state_showbox_locate[key][1]+40,str(value) if self.drone_state_chect[key][0] else '-',1.0)
            if cvui.button(self.frame, 150, 500, 'W'):
                self.put_action('W')
            if cvui.button(self.frame, 100, 540, 'A'):
                self.put_action('A')
            if cvui.button(self.frame, 150, 540, 'S'):
                self.put_action('S')
            if cvui.button(self.frame, 200, 540, 'D'):
                self.put_action('D')
            if cvui.button(self.frame, 400, 500, '8'):
                self.put_action('Up')
            if cvui.button(self.frame, 350, 540, '4'):
                self.put_action('Left')
            if cvui.button(self.frame, 400, 540, '5'):
                self.put_action('Down')
            if cvui.button(self.frame, 450, 540, '6'):
                self.put_action('Right')
            if cvui.button(self.frame, 350, 500, '7'):
                self.put_action('camera_down')
            if cvui.button(self.frame, 450, 500, '9'):
                self.put_action('camera_up')
            if cvui.button(self.frame, 500, 460, '-'):
                self.put_action('Speed_down')
            if cvui.button(self.frame, 500, 500, '+'):
                self.put_action('Speed_up')
            if cvui.button(self.frame, 100, 450, 'arm'):
                self.put_action('arm')
            if cvui.button(self.frame, 200, 450, 'takeoff'):
                self.put_action('takeoff')
            if cvui.button(self.frame, 320, 450, 'land'):
                self.put_action('land')
                    
            if keyboard.is_pressed("w"):
                self.put_action('W')
            if keyboard.is_pressed("a"):
                self.put_action('A')
            if keyboard.is_pressed("s"):
                self.put_action('S')
            if keyboard.is_pressed("d"):
                self.put_action('D')
            if keyboard.is_pressed("8"):
                self.put_action('Up')
            if keyboard.is_pressed("4"):
                self.put_action('Left')
            if keyboard.is_pressed("5"):
                self.put_action('Down')
            if keyboard.is_pressed("6"):
                self.put_action('Right')
            if keyboard.is_pressed("7"):
                self.put_action('camera_down')
            if keyboard.is_pressed("9"):
                self.put_action('camera_up')
            if keyboard.is_pressed("-"):
                self.put_action('Speed_down')
            if keyboard.is_pressed("+"):
                self.put_action('Speed_up')  
                
                
            self.command_data.command_to_socket(self.key_state)
            cvui.update()
            cv2.imshow(self.WINDOW_NAME, self.frame)
            if cv2.waitKey(20) == 27:
                self.key_state['end'] = True
                self.command_data.command_to_socket(self.key_state)
                self.save_data()
                self.auto_state = False
                cv2.destroyAllWindows()
                return 'end'

                
