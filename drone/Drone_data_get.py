import asyncio
from typing import Dict
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed
import math


class DRONE_DATA_GET:
    def __init__(self,drone : System) -> None:
        self.drone : System = drone
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
        
        
    def





async def print_drone_telemetry(drone):
    """
    드론의 위치 데이터, 배터리 잔량, yaw, pitch, roll 값, 비행 속력을 실시간으로 출력하는 함수
    """
    while True:
        # 위치 데이터 가져오기
        position = None
        async for pos in drone.telemetry.position():
            position = pos
            break
        
        # 배터리 잔량 가져오기
        battery = None
        async for bat in drone.telemetry.battery():
            battery = bat
            break

        # yaw, pitch, roll 가져오기
        attitude = None
        async for att in drone.telemetry.attitude_euler():
            attitude = att
            break

        # 속력 가져오기
        velocity = None
        speed = None
        async for vel in drone.telemetry.velocity_ned():
            velocity = vel
            speed = math.sqrt(
                vel.north_m_s**2 + vel.east_m_s**2 + vel.down_m_s**2
            )  # 총 속력 계산
            break

        # 출력: 한 줄로 깔끔하게 정리
        if position and battery and attitude and speed is not None:
            print(
                f"Lat: {position.latitude_deg:.6f}, Lon: {position.longitude_deg:.6f}, "
                f"Alt: {position.relative_altitude_m:.2f} m, "
                f"Battery: {battery.remaining_percent * 100:.2f}%, "
                f"Roll: {attitude.roll_deg:.2f}°, Pitch: {attitude.pitch_deg:.2f}°, Yaw: {attitude.yaw_deg:.2f}°, "
                f"Speed: {speed:.2f} m/s"
            )

        # 실시간 출력을 위해 짧은 대기
        await asyncio.sleep(1)

async def main():
    # 드론 객체 초기화 및 연결
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    # 텔레메트리 출력 태스크와 비행 명령 태스크를 병렬로 실행
    telemetry_task = asyncio.create_task(print_drone_telemetry(drone))
    flight_task = asyncio.create_task(perform_flight_operations(drone))

    # 두 태스크를 동시에 실행
    await asyncio.gather(telemetry_task, flight_task)


# 메인 함수 실행
if __name__ == "__main__":
    asyncio.run(main())

