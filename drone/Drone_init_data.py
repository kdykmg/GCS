import json
from typing import Dict
import time
import os

path=os.path.dirname(__file__)
path=path+''
os.chdir(path)
class DRONE_INIT_DATA:
    def __init__(self) -> None:
        self.drone_init_data_dic : Dict = dict(
            user_name='',
            drone_name='',
            server_ip='',
            server_port=0,
            drone_environment=1 # 0: real 1: virtual
        )
        self.init_load_data()
        

    def init_load_data(self) -> None:
        with open('drone_init_data.json','r') as f:
            try:
                loaded_data : Dict= json.load(f)
                for key, value in loaded_data.items():
                    self.drone_init_data_dic[key] = value
            except:
                print('fail load data')
    
    
    def save_data(self,data : Dict) -> None:
        for key, value in data.items():
            self.drone_init_data_dic[key]=value
            with open('drone_init_data.json','w') as f:
                json.dump(self.drone_init_data_dic,f) 
                
                
    def load_drone_init_data(self) -> Dict:
        return self.drone_init_data_dic