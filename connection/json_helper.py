import socket
import threading
import time
import struct
import json

ENCODING = 'utf-8'
HEADER = "!I"
HEADER_SIZE = struct.calcsize(HEADER)

def send_json(sock: socket.socket, obj: dict) -> None:
    payload = json.dumps(obj, separators=(",",":")).encode(ENCODING)
    header = struct.pack(HEADER,len(payload))
    sock.sendall(header+payload)

def recv_json(sock: socket.socket) -> dict:
    header = _recv_exact(sock, HEADER_SIZE)
    if not header:
        raise ConnectionError("socket closed")
    (length,) = struct.unpack(HEADER,header)
    payload = _recv_exact(sock,length)
    return json.loads(payload.decode(ENCODING))

def _recv_exact(sock: socket.socket, n: int) -> bytes:
    data = bytearray()
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)