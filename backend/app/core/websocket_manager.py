"""
WebSocket管理器 - WebSocket Connection Manager
管理客户端连接和实时消息推送
"""
import logging
import json
from datetime import datetime
from typing import List, Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 所有活跃连接
        self.active_connections: List[WebSocket] = []
        # 按股票代码分组的连接
        self.symbol_connections: Dict[str, Set[WebSocket]] = {}
        # 按用户分组的连接（如果需要用户认证）
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """接受新的WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # 从所有分组中移除
        for symbol, connections in self.symbol_connections.items():
            connections.discard(websocket)
        
        for user_id, connections in self.user_connections.items():
            connections.discard(websocket)
        
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")
    
    def subscribe_symbol(self, websocket: WebSocket, symbol: str):
        """订阅股票行情"""
        if symbol not in self.symbol_connections:
            self.symbol_connections[symbol] = set()
        self.symbol_connections[symbol].add(websocket)
        logger.debug(f"客户端订阅股票: {symbol}")
    
    def unsubscribe_symbol(self, websocket: WebSocket, symbol: str):
        """取消订阅股票行情"""
        if symbol in self.symbol_connections:
            self.symbol_connections[symbol].discard(websocket)
            logger.debug(f"客户端取消订阅股票: {symbol}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_symbol(self, symbol: str, message: dict):
        """广播消息给订阅了特定股票的客户端"""
        if symbol not in self.symbol_connections:
            return
        
        disconnected = []
        connections = list(self.symbol_connections[symbol])
        
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"发送股票消息失败: {symbol}, {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_alert(self, alert_data: dict):
        """
        发送预警消息
        
        Args:
            alert_data: 预警数据
                {
                    "type": "alert",
                    "symbol": "000001",
                    "stock_name": "平安银行",
                    "alert_type": "price_above",
                    "current_value": 12.5,
                    "threshold": 12.0,
                    "message": "价格突破设定值"
                }
        """
        message = {
            "channel": "alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 发送给订阅了该股票的客户端
        symbol = alert_data.get('symbol')
        if symbol:
            await self.broadcast_to_symbol(symbol, message)
        
        # 同时广播给所有客户端（预警需要全局通知）
        await self.broadcast(message)
    
    async def send_price_update(self, symbol: str, price_data: dict):
        """
        发送价格更新
        
        Args:
            symbol: 股票代码
            price_data: 价格数据
        """
        message = {
            "channel": "price",
            "symbol": symbol,
            "data": price_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_symbol(symbol, message)
    
    async def send_market_overview(self, data: dict):
        """发送市场概览更新"""
        message = {
            "channel": "market_overview",
            "data": data
        }
        await self.broadcast(message)
    
    def get_connection_stats(self) -> dict:
        """获取连接统计信息"""
        return {
            "total_connections": len(self.active_connections),
            "subscribed_symbols": len(self.symbol_connections),
            "symbol_subscriptions": {
                symbol: len(connections) 
                for symbol, connections in self.symbol_connections.items()
            }
        }


# 全局连接管理器实例
manager = ConnectionManager()
