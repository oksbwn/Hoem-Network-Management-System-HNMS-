from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
import asyncio
import paramiko
import logging
import json
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

class SSHSession:
    def __init__(self, host: str, port: int = 22, username: str = None, password: str = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.shell = None

    async def connect(self):
        try:
            await asyncio.to_thread(
                self.client.connect,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            self.shell = self.client.invoke_shell(term='xterm')
            self.shell.setblocking(0)
            return True
        except Exception as e:
            logger.error(f"SSH Connection failed: {e}")
            return False

    async def read(self):
        if self.shell and self.shell.recv_ready():
            return await asyncio.to_thread(self.shell.recv, 1024)
        return None

    async def write(self, data: str):
        if self.shell:
            await asyncio.to_thread(self.shell.send, data)

    def close(self):
        self.client.close()

@router.websocket("/ws/{ip}")
async def ssh_websocket_endpoint(websocket: WebSocket, ip: str):
    print(f"DEBUG: SSH WebSocket connection attempt for {ip}")
    await websocket.accept()
    print("DEBUG: WebSocket accepted")
    session: Optional[SSHSession] = None
    
    try:
        # 1. Wait for credentials
        print("DEBUG: Waiting for credentials...")
        auth_data = await websocket.receive_json()
        print(f"DEBUG: Received credentials: {auth_data.keys()}")
        username = auth_data.get("username")
        password = auth_data.get("password")
        port = auth_data.get("port", 22)

        session = SSHSession(ip, port, username, password)
        print(f"DEBUG: Connecting to SSH {ip}:{port}...")
        if await session.connect():
            print("DEBUG: SSH Connected Successfully")
            await websocket.send_text("\r\n*** Connected to " + ip + " ***\r\n")
        else:
            print("DEBUG: SSH Connection Failed")
            await websocket.send_text("\r\n*** Connection Failed ***\r\n")
            await websocket.close()
            return

        # 2. Loop for bi-directional communication
        # We need a way to run the read loop concurrently with the receive loop
        
        async def read_from_ssh():
            while True:
                try:
                    data = await session.read()
                    if data:
                        await websocket.send_bytes(data)
                    else:
                        await asyncio.sleep(0.01)
                except Exception as e:
                    break

        # Start the reader task
        reader_task = asyncio.create_task(read_from_ssh())

        # Main loop: read from websocket (user input) -> write to SSH
        while True:
            data = await websocket.receive_text()
            await session.write(data)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"SSH WebSocket Error: {e}")
    finally:
        if session:
            session.close()
