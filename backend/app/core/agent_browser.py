"""
Agent Browser - 浏览器代理模块

基于 Playwright 封装，用于模拟浏览器行为，处理动态 Token 和反爬虫机制。
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Response

logger = logging.getLogger(__name__)


class AgentBrowser:
    """
    Agent 浏览器封装
    
    功能:
    - 自动管理 Browser/Context/Page 生命周期
    - 自动处理 Cookie 和 Session
    - 模拟真实用户行为（User-Agent, Viewport 等）
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        
    def start(self):
        """启动浏览器"""
        if self._playwright:
            return
            
        logger.info("启动 Agent Browser...")
        try:
            self._playwright = sync_playwright().start()
            
            # 启动浏览器
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                # 添加一些防止检测的参数
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-position=0,0',
                    '--ignore-certificate-errors',
                ]
            )
            
            # 创建上下文，设置拟人化参数
            self._context = self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            # 添加防止 webdriver 检测的脚本
            self._context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            self._page = self._context.new_page()
            logger.info("Agent Browser 启动成功")
            
        except Exception as e:
            logger.error(f"Agent Browser 启动失败: {e}")
            self.close()
            raise e
        
    def close(self):
        """关闭浏览器资源"""
        if self._context:
            self._context.close()
            self._context = None
            
        if self._browser:
            self._browser.close()
            self._browser = None
            
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
            
        logger.info("Agent Browser 已关闭")

    @property
    def page(self) -> Page:
        """获取当前页面实例"""
        if not self._page:
            self.start()
        return self._page
        
    def goto(self, url: str, wait_until: str = 'domcontentloaded', timeout: int = 30000):
        """访问页面"""
        try:
            self.page.goto(url, wait_until=wait_until, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"访问页面失败 {url}: {e}")
            return False
            
    def get_api_data(self, url: str, wait_until: str = 'domcontentloaded') -> Optional[Dict]:
        """
        获取 API 数据
        
        有些 API 需要 referer 和 cookie，直接用 requests 很难模拟。
        使用 browser context 的 request 功能可以直接带上当前 session 的 cookie。
        """
        try:
            # 确保浏览器已启动
            if not self._page:
                self.start()
                
            # 使用 page.request (APIRequestContext) 发起请求
            # 它会自动带上 context 中的 cookie
            response = self.page.request.get(url)
            
            if response.ok:
                return response.json()
            else:
                logger.warning(f"API 请求失败: {url}, 状态码: {response.status}")
                return None
                
        except Exception as e:
            logger.error(f"获取 API 数据异常: {url}, 错误: {e}")
            return None

    def get_cookies(self) -> List[Dict]:
        """获取当前 Cookie"""
        if self._context:
            return self._context.cookies()
        return []
        
# 单例模式 (可选)
_agent_browser = None

def get_agent_browser(headless: bool = True) -> AgentBrowser:
    global _agent_browser
    if _agent_browser is None:
        _agent_browser = AgentBrowser(headless=headless)
    return _agent_browser
