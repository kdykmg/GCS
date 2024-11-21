import json
from typing import Dict
import os

path=os.path.dirname(__file__)
path=path+''
os.chdir(path)


class DRONE_DATA:
    def __init__(self) -> None:
        self.data_dic : Dict =dict(
            user_name='',
            drone_name='',
            gcs_port='',
            server_ip='',
            server_port=0,
            video=[False],
            speed=[False],
            location_latitude=[False],
            location_longitude=[False],
            altitude=[False],
            battery=[False],
            yaw=[False],
            pitch=[False],
            roll=[False]
        )
        self.drone_key_data : Dict = dict()
        
        self.init_load_data()
        self.drone_key_data_load()
        
        
    def init_load_data(self) -> None:
        with open('drone_data.json','r') as f:
            try:
                loaded_data : Dict= json.load(f)
                for key, value in loaded_data.items():
                    self.data_dic[key] = value
            except:
                print('fail load init data')
                
    
    def drone_key_data_load(self) -> None:
        with open('drone_key_data.json','r') as f:
            try:
                loaded_data : Dict= json.load(f)
                for key, value in loaded_data.items():
                    self.drone_key_data[key] = value
            except:
                print('fail load key data')
                
                            
    def save_data(self,data : Dict) -> None:
        for key, value in data.items():
            self.data_dic[key]=value
            with open('drone_data.json','w') as f:
                json.dump(self.data_dic,f)
    
    
    def load_drone_state_chect_data(self) -> Dict:
        return self.data_dic
    
    
    def load_drone_command_key_data(self) -> Dict:
        return self.drone_key_data
    
    