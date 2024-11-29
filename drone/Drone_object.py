import asyncio
import math
import time
import Drone_state_get
from typing import Dict, List
import Drone_command_data_get
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw
from mavsdk.gimbal import GimbalMode, ControlMode


class DRONE_OBJECT:
    def __init__(self, command_data_get: Drone_command_data_get.DRONE_COMMAND_DATA_GET, drone_state_stream: Drone_state_get.DRONE_STATE_GET) -> None:
        self.command_data_getter: Drone_command_data_get.DRONE_COMMAND_DATA_GET = command_data_get
        self.drone_state_stream: Drone_state_get.DRONE_STATE_GET = drone_state_stream
        self.drone: System
        
        # Movement flags
        self.W: bool = False  # move_forward
        self.S: bool = False  # move_backward
        self.A: bool = False  # move_left
        self.D: bool = False  # move_right
        self.Left: bool = False  # yaw_left
        self.Right: bool = False  # yaw_right
        self.Down: bool = False  # altitude_down
        self.Up: bool = False  # altitude_up
        self.camera_up: bool = False  # gimbal_up
        self.camera_down: bool = False  # gimbal_down
        
        # Control state flags
        self.control_active: bool = False
        self.gimbal_active: bool = False
        
        # Drone state flags
        self.arming_requested: bool = False
        self.takeoff_requested: bool = False
        self.land_requested: bool = False
        self.disarm_requested: bool = False
        self.comeback_requested: bool = False
        self.end_requested: bool = False
        
        # Drone status
        self.arming: bool = False
        self.landing: bool = True
        
        # Speed and movement parameters
        self.forward_speed: float = 2.0
        self.lateral_speed: float = 2.0
        self.vertical_speed: float = 2.0
        self.current_yaw_angle: float = 0.0
        self.current_gimbal_pitch: float = 0.0
        
        # Initial location tracking
        self.init_location: List[float] = [0, 0, 0]
        
        # State dictionary
        self.state: Dict = dict(
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
    
    async def stream_state(self) -> None:
        print("stream_state started")
        while not self.end_requested:
            try:
                self.drone_state_stream.drone_state_stream(self.state)
            except Exception as e:
                print(f"Error in stream_state: {e}")
            await asyncio.sleep(0.1)
        
    async def end_wait(self) -> None:
        print("end_wait started")
        while not self.end_requested:
            await asyncio.sleep(0.1)
        
        print("end_wait triggered")
        if not self.landing:
            self.comeback_requested = True
            await asyncio.sleep(0.1)
            
            while not self.landing:
                await asyncio.sleep(1)
            
            self.disarm_requested = True
            await asyncio.sleep(1)
            return
        
        if self.arming:
            self.disarm_requested = True
            await asyncio.sleep(1)
            return
        
        print("end_wait completed")
        
    async def update_drone_state(self) -> None:
        print('update_drone_state')
        while not self.end_requested:
            try:
                async for pos in self.drone.telemetry.position():
                    self.state['location_latitude'] = round(pos.latitude_deg, 6)
                    self.state['location_longitude'] = round(pos.longitude_deg, 6)
                    self.state['altitude'] = round(pos.relative_altitude_m, 2)
                    break
                async for bat in self.drone.telemetry.battery():
                    self.state['battery'] = round(bat.remaining_percent * 100, 2)
                    break
                async for att in self.drone.telemetry.attitude_euler():
                    self.state['yaw'] = round(att.yaw_deg, 2)
                    self.state['pitch'] = round(att.pitch_deg, 2)
                    self.state['roll'] = round(att.roll_deg, 2)
                    break
                async for vel in self.drone.telemetry.velocity_ned():
                    self.state['speed'] = round(math.sqrt(vel.north_m_s**2 + vel.east_m_s**2 + vel.down_m_s**2))
                print()
            except Exception as e:
                print(str(e))
                self.state['msg'] = str(e)
            await asyncio.sleep(0.1)
            
    async def get_command(self) -> None:
        print('get_command started')
        while not self.end_requested:
            try:
                command: Dict = self.command_data_getter.get_command()
                for key, value in command.items():
                    print(f"Command received: {key} = {value}")
                    if key == 'arm' and value:
                        self.arming_requested = True
                        await asyncio.sleep(0.1)
                        continue
                    elif key == 'takeoff' and value:
                        self.takeoff_requested = True
                        await asyncio.sleep(0.1)
                        continue
                    elif key == 'land' and value:
                        self.land_requested = True
                        await asyncio.sleep(0.1)
                        continue
                    elif key == 'disarm' and value:
                        self.disarm_requested = True
                        await asyncio.sleep(0.1)
                        continue
                    elif key == 'comeback' and value:
                        self.comeback_requested = True
                        await asyncio.sleep(0.1)
                        continue
                    elif key == 'Speed_up' and value:
                        self.forward_speed += 0.5
                        self.lateral_speed += 0.5
                        self.vertical_speed += 0.5
                    elif key == 'Speed_down' and value:
                        self.forward_speed = max(0.5, self.forward_speed - 0.5)
                        self.lateral_speed = max(0.5, self.lateral_speed - 0.5)
                        self.vertical_speed = max(0.5, self.vertical_speed - 0.5)
                    elif key == 'camera_up' or key == 'camera_down':
                        setattr(self, key, value)
                        self.gimbal_active = self.camera_up or self.camera_down
                    elif key == 'end':
                        self.end_requested = True
                    else:
                        setattr(self, key, value)
                        self.control_active = any([
                            self.W, self.S, self.A, self.D, 
                            self.Up, self.Down, 
                            self.Left, self.Right
                        ])
            except Exception as e:
                print(f"Error in get_command: {e}")
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
        
    async def arm_command(self) -> None:
        while not self.end_requested:
            if self.arming_requested and self.landing and not self.arming:
                await self.drone.action.arm()
                self.arming = True
                self.arming_requested = False
                await asyncio.sleep(1)
            await asyncio.sleep(0.1)
                
    async def takeoff_command(self) -> None:
        while not self.end_requested:
            if self.takeoff_requested and self.landing and self.arming:
                try:
                    await asyncio.wait_for(self.drone.action.takeoff(), timeout=10)
                except asyncio.TimeoutError:
                    print("Takeoff timed out.")
                await asyncio.sleep(3)
                self.landing = False
                self.takeoff_requested = False
                
                
                self.init_location = [
                    self.state['location_latitude'],
                    self.state['location_longitude'],
                    self.state['altitude']
                ]
                print('takeoff success')
                await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
                await self.drone.offboard.start()
                self.control_active = True
            await asyncio.sleep(0.1)
    
    async def land_command(self) -> None:
        while not self.end_requested:
            if self.land_requested and not self.landing:
                self.control_active = False
                await self.drone.action.land()
                self.landing = True
                self.land_requested = False
                await asyncio.sleep(5)
            await asyncio.sleep(0.1)
                
    async def disarm_command(self) -> None:
        while not self.end_requested:
            if self.disarm_requested and self.landing and self.arming:
                await self.drone.action.disarm()
                self.arming = False 
                self.disarm_requested = False
                await asyncio.sleep(1)
            await asyncio.sleep(0.1)
                
    async def comeback_command(self) -> None:
        while not self.end_requested:
            if self.comeback_requested and not self.landing:
                self.control_active = False
                await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
                await self.drone.action.goto_location(
                    self.init_location[0], 
                    self.init_location[1], 
                    self.init_location[2], 
                    0
                )
                await asyncio.sleep(1)
                await self.drone.action.land()
                self.landing = True
                self.comeback_requested = False
                await asyncio.sleep(5)
            await asyncio.sleep(0.1)
            
    async def control_gimbal(self) -> None:
        while not self.end_requested:
            if self.gimbal_active and self.arming:
                if self.camera_up:
                    self.current_gimbal_pitch += 2.0
                if self.camera_down:
                    self.current_gimbal_pitch -= 2.0
                self.current_gimbal_pitch = max(-90.0, min(30.0, self.current_gimbal_pitch))
                await self.drone.gimbal.set_pitch_and_yaw(self.current_gimbal_pitch, 0.0)
            await asyncio.sleep(0.1)
            
    async def move_drone(self) -> None:
        while not self.end_requested:
            if self.control_active:
                forward: float = (self.forward_speed if self.W else 0.0) + (-self.forward_speed if self.S else 0.0)
                lateral: float = (-self.lateral_speed if self.A else 0.0) + (self.lateral_speed if self.D else 0.0)
                vertical: float = (self.vertical_speed if self.Down else 0.0) + (-self.vertical_speed if self.Up else 0.0)
                print(forward,lateral,vertical)
                if self.Left:
                    self.current_yaw_angle -= 2.0
                if self.Right:
                    self.current_yaw_angle += 2.0

                await self.drone.offboard.set_velocity_ned( VelocityNedYaw(forward, lateral, vertical, self.current_yaw_angle) )
            else :
                await self.drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
            await asyncio.sleep(0.1)
            
        
    async def command_main(self) -> None:
        self.drone = System()
        await self.connect_drone()
        await self.set_gimbal_mode()
        
        tasks = [
            asyncio.create_task(self.update_drone_state()),
            asyncio.create_task(self.stream_state()),
            asyncio.create_task(self.arm_command()),
            asyncio.create_task(self.takeoff_command()),
            asyncio.create_task(self.land_command()),
            asyncio.create_task(self.disarm_command()),
            asyncio.create_task(self.comeback_command()),
            asyncio.create_task(self.move_drone()),
            asyncio.create_task(self.control_gimbal()),
            asyncio.create_task(self.get_command())
        ]
        
        print('end wait')
        await self.end_wait()
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()