"""
快速功能测试脚本
Quick Function Test

快速验证核心功能是否正常工作
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """测试所有模块导入"""
    print("📦 测试模块导入...")

    try:
        from app.core.config import settings
        print("  ✅ 配置模块")
    except Exception as e:
        print(f"  ❌ 配置模块: {e}")
        return False

    try:
        from app.services.market_data import get_market_data_service
        print("  ✅ 行情服务")
    except Exception as e:
        print(f"  ❌ 行情服务: {e}")
        return False

    try:
        from app.services.portfolio import PortfolioService
        print("  ✅ 持仓服务")
    except Exception as e:
        print(f"  ❌ 持仓服务: {e}")
        return False

    try:
        from app.services.news import NewsService
        print("  ✅ 新闻服务")
    except Exception as e:
        print(f"  ❌ 新闻服务: {e}")
        return False

    try:
        from app.services.ai_analysis import AIAnalysisService
        print("  ✅ AI 分析服务")
    except Exception as e:
        print(f"  ❌ AI 分析服务: {e}")
        return False

    return True


def test_market_data():
    """测试行情数据功能"""
    print("\n🔍 测试行情数据...")

    try:
        from app.services.market_data import get_market_data_service

        service = get_market_data_service()

        # 测试搜索
        print("  测试股票搜索...")
        results = service.search_stock("平安")
        if results:
            print(f"    ✅ 找到 {len(results)} 个结果")
            print(f"    示例: {results[0]['symbol']} - {results[0]['name']}")
        else:
            print("    ❌ 未找到结果")

        # 测试实时行情
        print("  测试实时行情...")
        realtime = service.get_realtime_price("000001")
        if realtime:
            print(f"    ✅ {realtime['name']}: ¥{realtime['price']} ({realtime['change_pct']:+.2f}%)")
        else:
            print("    ❌ 获取失败")

        # 测试 K 线
        print("  测试 K 线数据...")
        kline = service.get_kline_data("000001", "daily", 5)
        if kline:
            print(f"    ✅ 获取到 {len(kline)} 条数据")
            print(f"    最新: {kline[-1]['date']} 收盘价 {kline[-1]['close']}")
        else:
            print("    ❌ 获取失败")

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def test_database():
    """测试数据库连接"""
    print("\n💾 测试数据库...")

    try:
        from app.core.database import engine

        with engine.connect() as conn:
            result = conn.execute("SELECT 1").fetchone()
            print("  ✅ 数据库连接成功")
            return True

    except Exception as e:
        print(f"  ❌ 数据库连接失败: {e}")
        return False


def test_api():
    """测试 API 端点"""
    print("\n🌐 测试 API 端点...")

    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # 测试根路径
        response = client.get("/")
        if response.status_code == 200:
            print("  ✅ 根路径: " + response.json()['message'])
        else:
            print(f"  ❌ 根路径: {response.status_code}")

        # 测试 API 文档
        response = client.get("/docs")
        if response.status_code == 200:
            print("  ✅ API 文档可访问")
        else:
            print(f"  ❌ API 文档: {response.status_code}")

        # 测试股票搜索
        response = client.get("/api/v1/stock/search?keyword=000001")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 股票搜索: 找到 {data.get('count', 0)} 个结果")
        else:
            print(f"  ❌ 股票搜索: {response.status_code}")

        # 测试持仓列表
        response = client.get("/api/v1/portfolio/list")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 持仓列表: {len(data['data']['items'])} 个持仓")
        else:
            print(f"  ❌ 持仓列表: {response.status_code}")

        return True

    except Exception as e:
        print(f"  ❌ API 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("MVP v0.1 快速功能测试")
    print("=" * 60)

    results = []

    # 执行测试
    results.append(("模块导入", test_imports()))
    results.append(("数据库连接", test_database()))
    results.append(("行情数据", test_market_data()))
    results.append(("API 端点", test_api()))

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查配置。")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
