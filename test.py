import json
from typing import Dict
import os

path=os.path.dirname(__file__)
path=path+''
os.chdir(path)


key_state_before= dict(
            W=False,
            A=False,
            S=False,
            D=False,
            Up=False,
            Left=False,
            Down=False,
            Right=False,
            Speed_up=False,
            Speed_down=False,
            camera_up=False,
            camera_down=False,
            arm=False,
            takeoff=False,
            land=False,
            end=False
        )


with open('drone_key_data.json','w') as f:
    json.dump(key_state_before,f)