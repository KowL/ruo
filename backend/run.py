#!/usr/bin/env python3
"""
Run script for Ruo Stock Module
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    # 检测8000端口是否被占用，如果被占用则使用8080
    port = int(os.getenv("PORT", "0"))
    if port == 0:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("0.0.0.0", 8000))
            s.close()
            port = 8000
        except socket.error:
            port = 8080
            s.close()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   📊 Ruo Stock - 股票智能分析平台                             ║
║                                                              ║
║   Starting server on http://0.0.0.0:{port}                    ║
║                                                              ║
║   功能:                                                       ║
║   • 连板天梯 - 追踪连续涨停股票                               ║
║   • 题材库   - 市场概念热点追踪                               ║
║   • 板块分析 - 行业板块涨跌排行                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
