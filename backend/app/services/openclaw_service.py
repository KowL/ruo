"""
OpenClaw Gateway 服务
通过 HTTP API 调用 OpenClaw Gateway
"""
import httpx
import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator

logger = logging.getLogger(__name__)

# Gateway 配置 - 使用 host.docker.internal 访问宿主机
GATEWAY_URL = "http://host.docker.internal:18789"
GATEWAY_TOKEN = "134a8f52e1dd34881335f0b67a145283"
TIMEOUT = 120


class OpenClawService:
    """OpenClaw Gateway API 服务"""

    def __init__(self):
        self.base_url = GATEWAY_URL
        self.token = GATEWAY_TOKEN
        self.timeout = TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",
                },
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_agents(self) -> Dict[str, Any]:
        """获取 Agents 列表"""
        import subprocess
        import json as json_mod
        
        # 尝试使用 CLI 获取
        cli_paths = [
            "/usr/local/bin/openclaw",
            "/usr/bin/openclaw", 
            "openclaw",
        ]
        
        for cli_path in cli_paths:
            try:
                result = subprocess.run(
                    [cli_path, "agents", "list", "--json"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    try:
                        agents_data = json_mod.loads(result.stdout)
                    except:
                        continue
                        
                    agents = []
                    for agent in agents_data:
                        agents.append({
                            "id": agent.get("id"),
                            "name": agent.get("identityName") or agent.get("name"),
                            "emoji": agent.get("identityEmoji", "🤖"),
                            "description": f"{agent.get('name', '')} Agent",
                            "model": agent.get("model", ""),
                            "workspace": agent.get("workspace"),
                            "capabilities": [],
                            "isDefault": agent.get("isDefault", False),
                        })
                    return {"status": "success", "data": agents}
            except FileNotFoundError:
                continue
            except Exception as e:
                continue
        
        # 如果 CLI 不可用，返回预定义的 agents 列表
        agents = [
            {"id": "main", "name": "ruo", "emoji": "🐟", "description": "默认主代理", "model": "kimi-coding/k2p5", "capabilities": [], "isDefault": True},
            {"id": "coder", "name": "CTO", "emoji": "💻", "description": "代码助手", "model": "minimax-portal/MiniMax-M2.5", "capabilities": [], "isDefault": False},
            {"id": "trader", "name": "Trader", "emoji": "📈", "description": "交易员", "model": "minimax-portal/MiniMax-M2.5", "capabilities": [], "isDefault": False},
            {"id": "news", "name": "News", "emoji": "📰", "description": "新闻助手", "model": "minimax-portal/MiniMax-M2.5", "capabilities": [], "isDefault": False},
            {"id": "cxq_trader", "name": "陈小群", "emoji": "🐉", "description": "交易代理", "model": "kimi-coding/k2p5", "capabilities": [], "isDefault": False},
            {"id": "paopao", "name": "Paopao (泡泡)", "emoji": "🫧", "description": "泡泡助手", "model": "minimax-portal/MiniMax-M2.5", "capabilities": [], "isDefault": False},
        ]
        return {"status": "success", "data": agents}

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """获取单个 Agent 详情"""
        result = await self.list_agents()
        if result.get("status") == "error":
            return result
        for agent in result.get("data", []):
            if agent.get("id") == agent_id:
                return {"status": "success", "data": agent}
        return {"status": "error", "message": "Agent not found"}

    async def chat(
        self,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
        thinking: str = "medium",
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """发送消息（非流式）"""
        payload = {
            "model": f"openclaw:{agent_id}",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 4096,
        }
        
        if session_id:
            # 使用 session_id 作为 user 字段来保持会话
            payload["user"] = session_id

        try:
            response = await self.client.post(
                "/v1/chat/completions",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            return {
                "status": "success",
                "data": {
                    "sessionId": session_id or "",
                    "reply": content,
                    "thinking": thinking,
                    "usage": {
                        "inputTokens": usage.get("prompt_tokens", 0),
                        "outputTokens": usage.get("completion_tokens", 0),
                        "totalTokens": usage.get("total_tokens", 0),
                    },
                    "durationMs": 0,
                }
            }
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {"status": "error", "message": str(e)}

    async def chat_stream(
        self,
        agent_id: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """发送消息（流式）"""
        payload = {
            "model": f"openclaw:{agent_id}",
            "messages": [{"role": "user", "content": message}],
            "max_tokens": 4096,
            "stream": True,
        }
        
        if session_id:
            payload["user"] = session_id

        try:
            async with self.client.stream(
                "POST",
                "/v1/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()
                
                # 发送 start 事件
                yield f'data: {{"type": "start", "sessionId": "{session_id or ""}"}}\n\n'
                
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        yield f"data: {chunk}\n\n"
                        
        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            yield f'data: {{"type": "error", "message": "{str(e)}"}}\n\n'

    async def list_sessions(self, agent_id: str) -> Dict[str, Any]:
        """列出所有会话"""
        return {"status": "success", "data": []}

    async def get_session_messages(self, agent_id: str, session_id: str) -> Dict[str, Any]:
        """获取会话历史"""
        return {
            "status": "success",
            "data": {
                "sessionId": session_id,
                "agentId": agent_id,
                "messages": [],
                "createdAt": "",
                "updatedAt": "",
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            response = await self.client.get("/health", timeout=5)
            return {"status": "ok", "version": "2026.3.1"}
        except:
            return {"status": "error", "message": "Gateway unreachable"}


# 全局服务实例
openclaw_service = OpenClawService()
