import asyncio
from typing import Dict
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed
import Drone_socket
import math


class DRONE_STATE_GET:
    def __init__(self,drone_socket : Drone_socket.DRONE_SOCKET) -> None:
        self.drone_socket = drone_socket
        
        
    def drone_state_stream(self,state : Dict) -> None:
        self.drone_socket.state = state
