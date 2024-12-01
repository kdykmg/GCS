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
        self.key_setting : Dict = self.drone_data.load_key_setting()
        self.update_frame : np.ndarray = self.set_frame()
        self.frameRows: int = self.frame.shape[0]
        self.frameCols: int = self.frame.shape[1]
        self.auto_state : bool = True
        self.message_log : List[str] = ['']
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
        self.key_release : Dict[str,np.ndarray] = {}
        self.key_push : Dict[str,np.ndarray] = {}
        for key in self.key_state.keys():
            if key != 'end':
                self.key_release[key] = cv2.resize(cv2.imread(f'key_imgs/{key}_release.png'),(120,60) if key == 'arm' or key == 'takeoff' or key == 'land' or key == 'disarm' or key == 'comeback' else (80,50))
                self.key_push[key] = cv2.resize(cv2.imread(f'key_imgs/{key}_push.png'),(120,60) if key == 'arm' or key == 'takeoff' or key == 'land' or key == 'disarm' or key == 'comeback' else (80,50))
        self.drone_state_chect : Dict[str, List[bool]] ={}
        self.drone_state_chect_data : Dict = self.drone_data.load_drone_state_chect_data()
        for key in self.drone_state.keys():
            self.drone_state_chect[key] = self.drone_state_chect_data[key]
        self.check_box_start_point : List[int] =[1050,30]
        self.show_box_start_point : List[int] =[20,400]
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
            if self.frameCols-self.show_box_start_point[0]-self.show_box_gap[0]-240>0:
                self.show_box_gap[0] += 160
            else:
                self.show_box_gap[0]=0
                self.show_box_gap[1]+=90
        self.drone_state_chectbox_show : bool = False
        self.drone_state_data_show : bool = False
        
            
    def set_frame(self) -> np.ndarray:
        new_frame : np.ndarray = np.zeros((720, 1280, 3), np.uint8)
        new_frame[:] = (242, 242, 242)
        for items in self.key_setting.values():
            location : tuple = items['location']
            size : tuple = items['size']
            new_frame[location[1]:location[1]+size[1],location[0]:location[0]+size[0],:] = items['color']
        return new_frame
            
            
    def save_data(self) -> None:
        self.drone_data.save_data(self.drone_state_chect)
        if self.auto_state:
            threading.Timer(1, self.save_data).start()
        else: 
            return
    
    
    def update_drone_state(self) -> None:
        latest_drone_state_data: Dict[str,float] = self.state_data.get_drone_info_streaming()
        message : str = self.state_data.get_drone_msg_streaming()
        with self.lock:
            for key, value in self.drone_state_chect.items():
                if value[0]:
                    self.drone_state[key] = latest_drone_state_data[key]
                else:
                    self.drone_state[key] = 0.0
            if self.message_log[-1] != message and message !='':
                self.message_log.append(message)
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
            self.frame[:] = self.update_frame
            if self.drone_state_chect['video'][0]:
                img : np.ndarray = self.vid_streaming.get_vid()
            else :
                img : np.ndarray = self.not_show_img
            if cvui.button(self.frame, 10, 10, img, img, img):
                pass
            #cvui.rect(self.frame, 8, 8, 642, 362, 0x000000)
            map_img=self.drone_map.get_map()
            if cvui.button(self.frame, 670, 10, map_img, map_img, map_img):
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
            cvui.rect(self.frame, 4, 390, self.frameCols-8, 314, 0x000000, 0xcccccc)
            for key, value in self.drone_state.items():
                if key =='video': continue
                cvui.window(self.frame,self.drone_state_showbox_locate[key][0],self.drone_state_showbox_locate[key][1],120,75,key)
                cvui.text(self.frame,self.drone_state_showbox_locate[key][0]+10,self.drone_state_showbox_locate[key][1]+40,str(value) if self.drone_state_chect[key][0] else '-',0.5)
            cvui.window(self.frame, 980, 490, 280, 120, 'message')
            message : str = self.state_data.get_drone_msg_streaming()
            new_message : List =['']
            k : int = 0
            for i in range(len(message)) :
                if i %20 == 0 :
                    k +=1
                    new_message.append(message[i])
                else :
                    new_message[k] = new_message[k] + message[i]
            for i in range(k) :
                cvui.text(self.frame,1000, 500+ k*10,new_message[k],0.5)
            for key, items in self.key_setting.items():
                location : tuple = items['location']
                p_keyboard : str = items['keyboard']
                size : tuple = items['size']
                if size == [120,60] :
                    if cvui.button(self.frame, location[0], location[1], self.key_release[key],self.key_release[key],self.key_push[key]):
                        self.put_action(key)
                else :
                    if keyboard.is_pressed(p_keyboard):
                        self.put_action(key)
                        if cvui.button(self.frame, location[0], location[1], self.key_push[key],self.key_push[key],self.key_push[key]):
                            pass
                    else :
                        if cvui.button(self.frame, location[0], location[1], self.key_release[key],self.key_release[key],self.key_push[key]):
                            self.put_action(key)    
            
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

                
