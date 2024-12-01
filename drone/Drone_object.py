import asyncio
import math
import time
import Drone_state_get
import Drone_socket
import threading
from typing import Dict, List
import Drone_command_data_get
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityBodyYawspeed
from mavsdk.gimbal import GimbalMode, ControlMode


class DRONE_OBJECT:
    def __init__(self, command_data_get : Drone_command_data_get.DRONE_COMMAND_DATA_GET, drone_state_stream : Drone_state_get.DRONE_STATE_GET, drone_socket : Drone_socket.DRONE_SOCKET) -> None:
        self.command_data_getter : Drone_command_data_get.DRONE_COMMAND_DATA_GET = command_data_get
        self.drone_state_stream : Drone_state_get.DRONE_STATE_GET = drone_state_stream
        self.drone_socket : Drone_socket.DRONE_SOCKET = drone_socket
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
        self.control : bool = False
        self.gimbal : bool = False
        self.arm : bool = False
        self.arming : float = False
        self.takeoff : bool = False
        self.land : bool = False
        self.landing : float = True
        self.disarm : bool = False
        self.comeback : bool = False
        self.end : bool = False
        self.forward_speed : float = 2.0
        self.lateral_speed : float = 2.0
        self.vertical_speed : float = 2.0
        self.current_gimbal_pitch : float = 0.0
        self.init_location : List[float] = [0,0,0]
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
    
    
    def stream_state(self) -> None:
        print("stream_state started")
        while True:
            try:
                self.drone_state_stream.drone_state_stream(self.state)
            except Exception as e:
                print(f"Error in stream_state: {e}")  
            time.sleep(0.1)

        
    def get_command(self) ->None:
        print('get_command started')
        while True:
            try:
                command : Dict = self.command_data_getter.get_command()
                for key, value in command.items():
                    if key == 'end' :
                        self.control = False
                        self.end = True
                        time.sleep(1)
                    elif key == 'arm' or key == 'takeoff' or key == 'land' or key == 'disarm' or key == 'comeback' and value:
                        setattr(self, key, value)
                        time.sleep(1)
                        setattr(self, key, False)
                    elif key == 'Speed_up' and value:
                        self.forward_speed += 0.5
                        self.lateral_speed += 0.5
                        self.vertical_speed += 0.5
                        time.sleep(0.1)
                    elif key == 'Speed_down' and value:
                        self.forward_speed = max(0.5, self.forward_speed - 0.5)
                        self.lateral_speed = max(0.5, self.lateral_speed - 0.5)
                        self.vertical_speed = max(0.5, self.vertical_speed - 0.5)
                        time.sleep(0.1)
                    else :
                        self.moving = True
                        setattr(self, key, value)
                        time.sleep(0.1)
            except Exception as e:
                print(f"Error in get_command: {e}")
                
                        
    async def update_drone_state(self) -> None:
        print('update_drone_state started')
        while True:
            try:
                if self.end:
                    self.drone_socket.connect_cancle_command()
                    exit()
                async for pos in self.drone.telemetry.position():
                    self.state['location_latitude'] = round(pos.latitude_deg, 6)
                    self.state['location_longitude'] = round(pos.longitude_deg, 6)
                    self.state['altitude'] = round(pos.relative_altitude_m, 2)
                    break
                async for bat in self.drone.telemetry.battery():
                    self.state['battery'] = round(bat.remaining_percent * 100,2)
                    break
                async for att in self.drone.telemetry.attitude_euler():
                    self.state['yaw'] = round(att.yaw_deg ,2)
                    self.state['pitch'] = round(att.pitch_deg ,2)
                    self.state['roll'] = round(att.roll_deg ,2)
                    break
                async for vel in self.drone.telemetry.velocity_ned():
                    self.state['speed'] = round(math.sqrt(vel.north_m_s**2 + vel.east_m_s**2 + vel.down_m_s**2 ))
                    break
            except Exception as e:
                print(str(e))
                self.state['msg'] = str(e)
            await asyncio.sleep(0.1)
            
            
    async def connect_drone(self) -> None:
        print("Connecting to drone...")
        await self.drone.connect(system_address="udp://:14540")
        async for state in self.drone.core.connection_state():
            print(f"Connection state: {state.is_connected}")
            if state.is_connected:
                print("Drone connected successfully.")
                break
            await asyncio.sleep(1)
    
    
    async def set_gimbal_mode(self) -> None:
        await self.drone.gimbal.take_control(ControlMode.PRIMARY)
        await self.drone.gimbal.set_mode(GimbalMode.YAW_FOLLOW)
        
          
    async def drone_action(self) -> None:
        while True:
            try:
                if self.end:
                    return
                if self.landing and not self.arming and self.arm :
                    await self.drone.action.arm()
                    self.arming = True
                    await asyncio.sleep(1)
                    self.state['msg'] = 'arm success'
                    continue
                if self.landing and self.arming and self.takeoff :
                    await self.drone.action.takeoff()
                    self.landing = False
                    await asyncio.sleep(5)
                    self.init_location = [self.state['location_latitude'],self.state['location_longitude'],self.state['altitude']]
                    await self.set_gimbal_mode()
                    await self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
                    await self.drone.offboard.start()
                    self.control = True
                    self.state['msg'] = 'takeoff success'
                    continue
                if not self.landing and self.arming and self.land :
                    self.control =False
                    await self.drone.action.land()
                    self.landing = True
                    await asyncio.sleep(5)
                    self.state['msg'] = 'land success'
                if self.landing and self.arming and self.disarm :
                    await self.drone.action.disarm()
                    self.arming = False 
                    await asyncio.sleep(1)
                    self.state['msg'] = 'disarm success'
                if not self.landing and self.arming and self.comeback :
                    self.control = False
                    await self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
                    await self.drone.action.goto_location(self.init_location[0], self.init_location[1], self.state['altitude'], 0)
                    while True :
                        if abs(self.state['location_latitude'] - self.init_location[0]) < 0.000001 and \
                        abs(self.state['location_longitude'] - self.init_location[1]) < 0.000001 :
                            await self.drone.action.land()
                            break
                        await asyncio.sleep(1)
                        
                    await asyncio.sleep(1)
                    self.landing = True
                    await asyncio.sleep(5)
                    
                    self.state['msg'] = 'comeback success'
                if self.camera_up or self.camera_down:
                    if self.camera_up :
                        self.current_gimbal_pitch += 2.0
                    if self.camera_down:
                        self.current_gimbal_pitch -= 2.0
                    self.current_gimbal_pitch = max(-90.0, min(30.0, self.current_gimbal_pitch))
                    await self.drone.gimbal.set_pitch_and_yaw(self.current_gimbal_pitch, 0.0)
                if self.control :
                    forward : float = (self.forward_speed if self.W else 0.0) + (-self.forward_speed if self.S else 0.0)
                    lateral : float = (-self.lateral_speed if self.A else 0.0) + (self.lateral_speed if self.D else 0.0)
                    vertical : float = (self.vertical_speed if self.Down else 0.0) + (-self.vertical_speed if self.Up else 0.0)
                    if self.Left:
                        current_yaw_angle = -30.0
                    if self.Right:
                        current_yaw_angle = 30.0
                    if self.Left or self.Right:
                        await self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(forward, lateral, vertical, current_yaw_angle))
                    else :
                        await self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(forward, lateral, vertical, 0.0))
                if self.control:
                    if self.W or self.S or self.A or self.D or self.Left or self.Right or self.Down or self.Up :
                        pass
                    else :
                        await self.drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
            except Exception as e:
                print(str(e))
                self.state['msg'] = str(e)
            await asyncio.sleep(0.1) 
   
   
    async def command_main(self) -> None:
        self.drone = System()
        await self.connect_drone()
        command_thread : threading.Thread = threading.Thread(target=self.get_command)
        command_thread.daemon=True
        command_thread.start()
        state_thread : threading.Thread = threading.Thread(target=self.stream_state)
        state_thread.daemon=True
        state_thread.start()
        await asyncio.gather(self.update_drone_state(), self.drone_action())