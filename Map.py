import cv2
import threading
import numpy as np
import requests
import time
import Drone_state
import math
from typing import Tuple, Dict, Optional


class MAP:
    def __init__(self, drone_state_streaming: Drone_state.DRONE_STATE) -> None:
        self.state_data: Drone_state.DRONE_STATE = drone_state_streaming
        self.fps: int = 30
        self.zoom: int = 15
        self.tile_size: int = 256
        self.display_size: int = 256
        self.buffer_size: int = 768
        self.tile_buffer: Dict[Tuple[int, int], np.ndarray] = {}
        self.current_tile: Tuple[int, int] = (0, 0)
        self.lock: threading.Lock = threading.Lock()
        self.drone_pos: list[float] = [0.0, 0.0]
        self.global_pixel_x: int = 0
        self.global_pixel_y: int = 0
        self.tile_server: str = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DroneGCS/1.0'
        })
        self.buffer_image: np.ndarray = np.ones((self.buffer_size, self.buffer_size, 3), dtype=np.uint8) * 255
        self.map_img: np.ndarray = np.zeros((360, 360, 3), np.uint8)
        
        self.map_thread: threading.Thread = threading.Thread(target=self.update_map)
        self.map_thread.daemon = True
        self.map_thread.start()
        
        
    def deg_to_tile(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[float, float]:
        lat_rad: float = math.radians(lat_deg)
        n: float = 2.0 ** zoom
        x_tile: float = (lon_deg + 180.0) / 360.0 * n
        y_tile: float = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
        return x_tile, y_tile
    
    
    def load_tile(self, tile_x: int, tile_y: int) -> np.ndarray:
        try:
            url: str = self.tile_server.format(z=self.zoom, x=int(tile_x), y=int(tile_y))
            response: requests.Response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                image_data: np.ndarray = np.asarray(bytearray(response.content), dtype=np.uint8)
                tile: np.ndarray = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
                return tile
            else:
                return np.ones((self.tile_size, self.tile_size, 3), dtype=np.uint8) * 200
        except:
            return np.ones((self.tile_size, self.tile_size, 3), dtype=np.uint8) * 200
        
        
    def update_buffer_image(self, center_tile_x: float, center_tile_y: float) -> None:
        with self.lock:
            self.buffer_image.fill(200)
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    tile_x: int = int(center_tile_x) + dx
                    tile_y: int = int(center_tile_y) + dy
                    tile_pos: Tuple[int, int] = (tile_x, tile_y)
                    if tile_pos not in self.tile_buffer:
                        self.tile_buffer[tile_pos] = self.load_tile(tile_x, tile_y)
                    tile: Optional[np.ndarray] = self.tile_buffer[tile_pos]
                    if tile is not None:
                        y_start: int = (dy + 1) * self.tile_size
                        x_start: int = (dx + 1) * self.tile_size
                        self.buffer_image[y_start:y_start + self.tile_size, x_start:x_start + self.tile_size] = tile
            
            keys_to_remove: list = []
            for tile_pos in self.tile_buffer:
                if abs(tile_pos[0] - int(center_tile_x)) > 1 or abs(tile_pos[1] - int(center_tile_y)) > 1:
                    keys_to_remove.append(tile_pos)
            for key in keys_to_remove:
                del self.tile_buffer[key]
                
                
    def update_drone_position(self, lat: float, lon: float) -> None:
        self.drone_pos = [lon, lat]
        tile_x, tile_y = self.deg_to_tile(lat, lon, self.zoom)
        n: float = 2.0 ** self.zoom
        self.global_pixel_x = int((lon + 180.0) / 360.0 * n * self.tile_size)
        self.global_pixel_y = int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n * self.tile_size)
        if (int(tile_x), int(tile_y)) != self.current_tile:
            self.current_tile = (int(tile_x), int(tile_y))
            self.update_buffer_image(tile_x, tile_y)
    

    def render_map(self) -> np.ndarray:
        local_x: int = self.global_pixel_x % self.tile_size + self.tile_size
        local_y: int = self.global_pixel_y % self.tile_size + self.tile_size
        x_start: int = local_x - self.display_size//2
        y_start: int = local_y - self.display_size//2
        x_end: int = x_start + self.display_size
        y_end: int = y_start + self.display_size
        map_img: np.ndarray = self.buffer_image[y_start:y_end, x_start:x_end].copy()
        cv2.circle(map_img, (self.display_size//2, self.display_size//2), 2, (0, 0, 255), -1)
        map_img = cv2.resize(map_img, (360,360), interpolation=cv2.INTER_LINEAR)
        return map_img
    
    
    def update_map(self) -> None:
        while True:
            try:
                start_time: float = time.time()
                latitude, longitude = self.state_data.get_drone_location_streaming()
                self.update_drone_position(latitude, longitude)
                self.map_img = self.render_map()
                time.sleep(max(0, 1/self.fps - (time.time() - start_time)))
            except:
                cv2.putText(self.map_img, 'map load false', (100,180), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            
            
    def get_map(self) -> np.ndarray:
        return self.map_img