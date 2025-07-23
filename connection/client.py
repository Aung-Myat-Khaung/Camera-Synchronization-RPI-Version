import socket
from . import json_helper

class Client_Com:
    def __init__(self, host, port):
        self.addr = (host, port)

    def send_camera_data(self, ball_id: str, color: str):
        try:
            with socket.create_connection(self.addr) as sock:
                packet = {
                    "id": ball_id,
                    "color": color,
                }
                json_helper.send_json(sock, packet)
                print("Error")
        except Exception as e:
            print(f"[Error] Failed to send data {e}")  
