"""
OpenClaw API 端点
通过 Gateway HTTP API 与 OpenClaw 集成
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from app.services.openclaw_service import openclaw_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================================
# DTO 模型
# ========================================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None
    thinking: str = "medium"
    timeout: Optional[int] = None


class ChatStreamRequest(BaseModel):
    """流式聊天请求"""
    message: str
    session_id: Optional[str] = None


# ========================================
# API 端点
# ========================================

@router.get("/agents")
async def list_agents():
    """
    获取 Agents 列表
    """
    try:
        result = await openclaw_service.list_agents()
        return result
    except Exception as e:
        logger.error(f"获取 Agents 列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """
    获取单个 Agent 详情
    """
    try:
        result = await openclaw_service.get_agent(agent_id)
        return result
    except Exception as e:
        logger.error(f"获取 Agent {agent_id} 详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/chat")
async def chat(agent_id: str, request: ChatRequest):
    """
    发送消息（非流式）
    """
    try:
        result = await openclaw_service.chat(
            agent_id=agent_id,
            message=request.message,
            session_id=request.session_id,
            thinking=request.thinking,
            timeout=request.timeout or 120,
        )
        return result
    except Exception as e:
        logger.error(f"聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/chat/stream")
async def chat_stream(agent_id: str, request: ChatStreamRequest):
    """
    发送消息（流式）
    """
    try:
        return StreamingResponse(
            openclaw_service.chat_stream(
                agent_id=agent_id,
                message=request.message,
                session_id=request.session_id,
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"流式聊天失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/sessions")
async def list_sessions(agent_id: str):
    """
    列出所有会话
    """
    try:
        result = await openclaw_service.list_sessions(agent_id)
        return result
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/sessions/{session_id}/messages")
async def get_session_messages(agent_id: str, session_id: str):
    """
    获取会话历史
    """
    try:
        result = await openclaw_service.get_session_messages(agent_id, session_id)
        return result
    except Exception as e:
        logger.error(f"获取会话历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
