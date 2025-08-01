import socket
from . import json_helper
import threading
from config.config import available_ID
HOST = socket.gethostbyname(socket.gethostname())
PORT = 5050

class Sever_Com:
    def __init__(self):
            server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            server.bind((HOST,PORT))
            server.listen()
            print(f"[Listening] {HOST} : {PORT}")
            while True:
                conn, addr = server.accept()
                threading.Thread(target=self.handle,args=(conn,addr),daemon=True).start()
    def handle (self,conn,addr):
        with conn:
            while True:
                try:
                    msg = json_helper.recv_json(conn)
                except ConnectionError:
                    break
                available_ID[msg["id"]] = {
                    "id": msg["id"],
                    "color": msg["color"]
                }
                print (available_ID)

                



