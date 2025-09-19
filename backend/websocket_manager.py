from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}  # user_id -> [websockets]

    async def connect(self, websocket: WebSocket, user_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)

        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Envia mensagem para todas as conexões ativas"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")
                self.active_connections.remove(connection)

    async def send_to_user(self, user_id: str, message: str):
        """Envia mensagem para um usuário específico"""
        if user_id in self.user_connections:
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    print(f"Erro ao enviar mensagem para usuário {user_id}: {e}")
                    self.user_connections[user_id].remove(websocket)

    async def broadcast_alert(self, alert_data: dict):
        """Envia alerta para todas as conexões ativas"""
        message = {
            "type": "alert",
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(message))

    async def send_device_update(self, device_id: int, update_data: dict):
        """Envia atualização de dispositivo"""
        message = {
            "type": "device_update",
            "device_id": device_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(message))

    async def send_threshold_alert(self, threshold_id: int, violation_data: dict):
        """Envia alerta de threshold violado"""
        message = {
            "type": "threshold_alert",
            "threshold_id": threshold_id,
            "data": violation_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(json.dumps(message))

# Instância global do gerenciador de conexões
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: str = None):
    """
    Endpoint WebSocket para notificações em tempo real
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Mantém a conexão viva e aguarda mensagens do cliente
            data = await websocket.receive_text()
            # Pode processar mensagens do cliente aqui se necessário
            print(f"Mensagem recebida de {user_id}: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"Cliente {user_id} desconectado")

    except Exception as e:
        print(f"Erro na conexão WebSocket: {e}")
        manager.disconnect(websocket, user_id)
