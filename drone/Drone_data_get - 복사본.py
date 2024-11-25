import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed
import math


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


async def perform_flight_operations(drone):
    """
    드론의 비행 명령(시동, 이륙, 고도 상승, 착륙)을 수행하는 함수
    """
    print("Arming the drone...")
    await drone.action.arm()
    await asyncio.sleep(2)  # 잠시 대기

    print("Taking off...")
    await drone.action.takeoff()
    await asyncio.sleep(5)  # 이륙 대기

    print("Climbing 10 meters...")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, -1.0, 0.0))
    await drone.offboard.start()
    await asyncio.sleep(10)  # 약 10초 동안 상승
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))  # 정지
    await asyncio.sleep(2)  # 잠시 대기

    print("Hovering for 5 seconds...")
    await asyncio.sleep(5)

    print("Landing...")
    await drone.action.land()
    await asyncio.sleep(10)  # 착륙 시간 대기


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

