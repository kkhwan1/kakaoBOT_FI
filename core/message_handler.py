"""
메시지 핸들러 모듈
메시지 전송 및 처리 관련 기능
"""

import json
from socket import socket, AF_INET, SOCK_STREAM


def send_message(room: str, msg: str):
    """카카오톡 메시지 전송 함수
    
    Args:
        room: 방 이름
        msg: 전송할 메시지
    """
    ip = "172.30.1.25"
    port = 4006

    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((ip, port))
    data = {
        "room": room,
        "msg": msg
    }
    client_socket.send(json.dumps(data).encode("utf-8"))
    client_socket.close()