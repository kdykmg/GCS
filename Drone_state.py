from typing import Dict, List
import Socket

class DRONE_STATE:
    def __init__(self, streaming_socket : Socket.SOCKET) -> None:
        self.streaming_socket : Socket.SOCKET = streaming_socket
        
        
    def get_drone_info_streaming(self) -> Dict[str,float]:
        drone_state_data : Dict = self.streaming_socket.state
        return {key: value for key, value in drone_state_data.items() if key != 'msg'}
    
    
    def get_drone_location_streaming(self) -> List[float]:
        drone_state_data : Dict = self.streaming_socket.state
        latitude : float = drone_state_data['location_latitude']
        longitude : float = drone_state_data['location_longitude']
        return [latitude,longitude]
    
    
    def get_drone_msg_streaming(self) -> str:
        drone_state_data : Dict = self.streaming_socket.state
        message : str = drone_state_data['msg']
        return message