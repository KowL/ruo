"""
WebSocket API - 实时数据推送
"""
import logging
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.core.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket连接端点
    
    连接后可以通过发送JSON消息进行订阅：
    - 订阅股票: {"action": "subscribe", "symbols": ["000001", "000002"]}
    - 取消订阅: {"action": "unsubscribe", "symbols": ["000001"]}
    - 心跳: {"action": "ping"}
    
    接收的消息类型：
    - 价格更新: {"channel": "price", "symbol": "000001", "data": {...}}
    - 预警通知: {"channel": "alert", "data": {...}}
    - 市场概览: {"channel": "market_overview", "data": {...}}
    """
    await manager.connect(websocket)
    
    try:
        # 发送连接成功消息
        await manager.send_personal_message({
            "channel": "system",
            "type": "connected",
            "message": "WebSocket连接成功"
        }, websocket)
        
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get('action')
                
                if action == 'subscribe':
                    # 订阅股票行情
                    symbols = message.get('symbols', [])
                    for symbol in symbols:
                        manager.subscribe_symbol(websocket, symbol)
                    
                    await manager.send_personal_message({
                        "channel": "system",
                        "type": "subscribed",
                        "symbols": symbols
                    }, websocket)
                    
                elif action == 'unsubscribe':
                    # 取消订阅
                    symbols = message.get('symbols', [])
                    for symbol in symbols:
                        manager.unsubscribe_symbol(websocket, symbol)
                    
                    await manager.send_personal_message({
                        "channel": "system",
                        "type": "unsubscribed",
                        "symbols": symbols
                    }, websocket)
                    
                elif action == 'ping':
                    # 心跳响应
                    await manager.send_personal_message({
                        "channel": "system",
                        "type": "pong",
                        "timestamp": message.get('timestamp')
                    }, websocket)
                    
                elif action == 'get_stats':
                    # 获取连接统计
                    stats = manager.get_connection_stats()
                    await manager.send_personal_message({
                        "channel": "system",
                        "type": "stats",
                        "data": stats
                    }, websocket)
                    
                else:
                    await manager.send_personal_message({
                        "channel": "system",
                        "type": "error",
                        "message": f"未知action: {action}"
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "channel": "system",
                    "type": "error",
                    "message": "无效的JSON格式"
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket处理错误: {e}")
        manager.disconnect(websocket)
