import asyncio
import threading
from typing import Dict
import Drone_command_data_get
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw
from mavsdk.gimbal import GimbalMode, ControlMode

class DRONE_COMMAND:
    def __init__(self, command_data_get : Drone_command_data_get.DRONE_COMMAND_DATA_GET) -> None:
        self.command_data_getter : Drone_command_data_get.DRONE_COMMAND_DATA_GET = command_data_get
        self.drone : System
        self.W : bool = False #move_forward
        self.S : bool = False #move_backward
        self.A : bool = False #move_left
        self.D : bool = False #move_right
        self.Left : bool = False #yaw_left
        self.Right : bool = False #yaw_right
        self.Down : bool = False #altitude_down
        self.Up : bool = False #altitude_up
        self.camera_up : bool = False #gimbal_up
        self.camera_down : bool = False #gimbal_down
        self.control : threading.Event = threading.Event()
        self.control_state : bool = False
        self.gimbal : threading.Event = threading.Event()
        self.gimbal_state : bool = False
        self.arm : threading.Event = threading.Event()
        self.takeoff : threading.Event = threading.Event()
        self.forward_speed : float = 2.0
        self.lateral_speed : float = 2.0
        self.vertical_speed : float = 2.0
        self.current_yaw_angle : float = 0.0
        self.current_gimbal_pitch : float = 0.0
        
        
    async def get_command(self) ->None:
        while 1:
            command : Dict = self.command_data_getter.get_command()
            for key, value in command.items():
                if key == 'arm' and value:
                    self.arm.set()
                    await asyncio.sleep(0.1)
                    self.arm.clear()
                    continue
                elif key == 'takeoff' and value:
                    self.arm.set()
                    await asyncio.sleep(0.1)
                    self.arm.clear()
                    continue
                elif key == 'land' and value:
                    self.arm.set()
                    await asyncio.sleep(0.1)
                    self.arm.clear()
                    continue
                elif key == 'Speed_up' and value:
                    self.forward_speed += 0.5
                    self.lateral_speed += 0.5
                    self.vertical_speed += 0.5
                elif key == 'Speed_up' and value:
                    self.forward_speed = max(0.5, self.forward_speed - 0.5)
                    self.lateral_speed = max(0.5, self.lateral_speed - 0.5)
                elif key == 'camera_up' or key == 'camera_up':
                    setattr(self, key, value)
                    if self.camera_up or self.camera_down:
                        if self.gimbal_state == False:
                            self.gimbal.set()
                            self.gimbal_state = True
                    elif self.gimbal_state ==True:
                        self.gimbal_state = False
                        self.gimbal.clear()
                elif key == 'end' :
                    pass # end 추가
                else :
                    setattr(self, key, value)
                    if self.W or  self.S or self.A or self.D or self.Up or self.Down or self.Left or self.Right:
                        if self.control_state == False:
                            self.control.set()
                            self.control_state = True
                    elif self.control_state == True:
                        self.control_state = False
                        self.control.clear()
                        
    
    async def connect_drone(self) -> None:
        await self.drone.connect(system_address="udp://:14540")
        async for state in self.drone.core.connection_state():
            await asyncio.sleep(1)
            if state.is_connected:
                break
    
    
    async def set_gimbal_mode(self) -> None:
        await self.drone.gimbal.take_control(ControlMode.PRIMARY)
        await self.drone.gimbal.set_mode(GimbalMode.YAW_FOLLOW)
    
    
    async def arm_and_takeoff(self) -> None:
        self.arm.wait()
        await self.drone.action.arm()
        self.takeoff.wait()
        await self.drone.action.takeoff()
        self.arm.clear()    
        self.takeoff.clear()    
        await asyncio.sleep(5)
    
    
    async def control_gimbal(self) -> None:
        while 1:
            self.arm.wait()
            if self.camera_up:
                self.current_gimbal_pitch += 2.0
            if self.camera_down:
                self.current_gimbal_pitch -= 2.0
            self.current_gimbal_pitch = max(-90.0, min(30.0, self.current_gimbal_pitch))
            await self.drone.gimbal.set_pitch_and_yaw(self.current_gimbal_pitch, 0.0)
            await asyncio.sleep(0.1)
            
            
    async def move_drone(self) -> None:
        while 1:
            self.control.wait()
            forward : float = self.forward_speed if self.W else 0.0 + -self.forward_speed if self.S else 0.0
            lateral : float = -self.lateral_speed if self.A else 0.0 + self.lateral_speed if self.D else 0.0
            vertical : float = self.vertical_speed if self.Down else 0.0 + -self.vertical_speed if self.Up else 0.0
            if self.Left:
                self.current_yaw_angle -= 2.0
            if self.Right:
                self.current_yaw_angle += 2.0  
            await self.drone.offboard.set_velocity_ned(VelocityNedYaw(forward, lateral, vertical, self.current_yaw_angle))
            await asyncio.sleep(0.1)
        
        
    async def command_main(self) -> None:
        await self.connect_drone()
        await self.set_gimbal_mode()
        await self.arm_and_takeoff()
        await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
        await self.drone.offboard.start()
        await asyncio.gather(self.move_drone(), self.control_gimbal(), self.get_command())