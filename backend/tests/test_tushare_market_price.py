"""
Tushare 行情数据拉取测试脚本
测试 market_price_tasks.py 中 _fetch_and_save 的 Tushare 数据拉取逻辑
不依赖数据库/Celery，直接验证 Tushare API 可用性与数据格式

用法:
    cd backend
    uv run python tests/test_tushare_market_price.py
"""
import sys
import os
from pathlib import Path

# 加载 .env 环境变量 (才能读到 TUSHARE_TOKEN)
from dotenv import load_dotenv
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file)
print(env_file)
print(os.getenv("TUSHARE_TOKEN"))
# 添加 backend 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import tushare as ts
from datetime import date, timedelta

# ─────────────────────────────────────────────
# 测试配置
# ─────────────────────────────────────────────
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")
TUSHARE_HTTP_URL = "http://lianghua.nanyangqiankun.top"   # 自定义转发域名

# 测试用股票（日线/周线/月线）
TEST_SYMBOLS = [
    ("000001", "SZ", "平安银行"),  # 深交所主板
    ("600036", "SH", "招商银行"),  # 上交所主板
    ("300750", "SZ", "宁德时代"),  # 创业板
]

TODAY = date.today().strftime("%Y%m%d")
# 本周一（用于 celery 任务 sync_weekly_price_task）
START_WEEKLY_TASK = (date.today() - timedelta(days=date.today().weekday())).strftime("%Y%m%d")
# 本月1日（用于 celery 任务 sync_monthly_price_task）
START_MONTHLY_TASK = date.today().replace(day=1).strftime("%Y%m%d")
# 周线/月线 tushare 在当周/当月结束后才生成，测试时用过去4周/3个月确保有数据
START_WEEKLY_TEST = (date.today() - timedelta(weeks=4)).strftime("%Y%m%d")
START_MONTHLY_TEST = (date.today() - timedelta(days=90)).strftime("%Y%m%d")
START_10Y = date.today().replace(year=date.today().year - 10).strftime("%Y%m%d")

PASS = 0
FAIL = 0


def _ts_code(symbol: str, market: str) -> str:
    return f"{symbol}.{market}"


def _init_pro():
    """初始化 Tushare Pro API（含自定义域名）"""
    if not TUSHARE_TOKEN:
        raise RuntimeError("TUSHARE_TOKEN 未配置，请检查 .env 文件")
    pro = ts.pro_api(TUSHARE_TOKEN)
    pro._DataApi__token = TUSHARE_TOKEN
    pro._DataApi__http_url = TUSHARE_HTTP_URL
    return pro


def _check_df(df, label: str) -> bool:
    """检查 DataFrame 是否合法，打印摘要"""
    global PASS, FAIL
    if df is None or df.empty:
        print(f"  ❌ {label}: 返回空数据")
        FAIL += 1
        return False

    required_cols = {"trade_date", "open", "high", "low", "close", "vol", "amount", "pct_chg", "change"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"  ⚠️  {label}: 缺少列 {missing}（已有 {list(df.columns)}）")
        FAIL += 1
        return False

    latest = df.iloc[0]  # Tushare 默认最新在前
    print(f"  ✅ {label}: {len(df)} 条记录 | 最新 trade_date={latest['trade_date']}"
          f"  open={latest['open']}  close={latest['close']}  pct_chg={latest['pct_chg']:.2f}%")
    PASS += 1
    return True


def _check_data_format(df, label: str):
    """验证数据格式转换逻辑（与 _fetch_and_save 中一致）"""
    global PASS, FAIL
    errors = 0
    parsed = []
    for _, row in df.iterrows():
        try:
            t_date = str(row["trade_date"])
            formatted_date = f"{t_date[:4]}-{t_date[4:6]}-{t_date[6:]}"
            parsed.append({
                "date": formatted_date,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["vol"]) * 100,
                "amount": float(row["amount"]) * 1000,
                "change": float(row["change"]),
                "changePct": float(row["pct_chg"]),
                "turnover": 0.0,
            })
        except Exception as e:
            errors += 1
            print(f"    解析行出错: {e}")

    if errors == 0:
        print(f"  ✅ {label} 数据格式转换: {len(parsed)} 条全部成功")
        PASS += 1
    else:
        print(f"  ❌ {label} 数据格式转换: {errors} 条失败 / {len(df)} 条")
        FAIL += 1

    return parsed


# ─────────────────────────────────────────────
# 测试用例
# ─────────────────────────────────────────────

def test_token_config():
    """验证 TUSHARE_TOKEN 已配置"""
    print("\n[1] 验证 TUSHARE_TOKEN 配置")
    global PASS, FAIL
    if TUSHARE_TOKEN and len(TUSHARE_TOKEN) > 10:
        print(f"  ✅ token 已配置: {TUSHARE_TOKEN[:8]}...（长度 {len(TUSHARE_TOKEN)}）")
        PASS += 1
    else:
        print(f"  ❌ token 未配置或过短: '{TUSHARE_TOKEN}'")
        FAIL += 1


def test_symbol_mapping():
    """验证 symbol -> ts_code 转换逻辑"""
    print("\n[2] 验证 symbol -> ts_code 映射逻辑")
    global PASS, FAIL
    cases = [
        ("600036", "600036.SH"),
        ("000001", "000001.SZ"),
        ("300750", "300750.SZ"),
        ("430047", "430047.BJ"),
        ("835975", "835975.BJ"),
    ]
    ok = True
    for symbol, expected in cases:
        if symbol.startswith("6"):
            result = f"{symbol}.SH"
        elif symbol.startswith("0") or symbol.startswith("3"):
            result = f"{symbol}.SZ"
        elif symbol.startswith("4") or symbol.startswith("8"):
            result = f"{symbol}.BJ"
        else:
            result = symbol
        status = "✅" if result == expected else "❌"
        if result != expected:
            ok = False
        print(f"  {status} {symbol} -> {result} (期望: {expected})")
    if ok:
        PASS += 1
    else:
        FAIL += 1


def test_daily_data(pro):
    """测试日线数据拉取（最近一周）"""
    print("\n[3] 测试日线数据拉取（最近一周）")
    start = (date.today() - timedelta(days=7)).strftime("%Y%m%d")
    for symbol, market, name in TEST_SYMBOLS:
        ts_code = _ts_code(symbol, market)
        try:
            df = pro.daily(ts_code=ts_code, start_date=start, end_date=TODAY)
            if _check_df(df, f"日线 {ts_code} {name}"):
                _check_data_format(df, f"日线格式 {ts_code}")
        except Exception as e:
            global FAIL
            print(f"  ❌ 日线拉取异常 {ts_code}: {e}")
            FAIL += 1


def test_weekly_data(pro):
    """测试周线数据拉取（过去4周，已完成的完整周期）"""
    print(f"\n[4] 测试周线数据拉取（{START_WEEKLY_TEST} ~ {TODAY}，过去4周）")
    print(f"     注：celery 任务实际使用本周一({START_WEEKLY_TASK})起始，当周结束前 tushare 无周线数据")
    for symbol, market, name in TEST_SYMBOLS:
        ts_code = _ts_code(symbol, market)
        try:
            df = pro.weekly(ts_code=ts_code, start_date=START_WEEKLY_TEST, end_date=TODAY)
            _check_df(df, f"周线 {ts_code} {name}")
        except Exception as e:
            global FAIL
            print(f"  ❌ 周线拉取异常 {ts_code}: {e}")
            FAIL += 1


def test_monthly_data(pro):
    """测试月线数据拉取（过去3个月，已完成的完整月份）"""
    print(f"\n[5] 测试月线数据拉取（{START_MONTHLY_TEST} ~ {TODAY}，过去3个月）")
    print(f"     注：celery 任务实际使用本月1日({START_MONTHLY_TASK})起始，当月结束前 tushare 无月线数据")
    for symbol, market, name in TEST_SYMBOLS:
        ts_code = _ts_code(symbol, market)
        try:
            df = pro.monthly(ts_code=ts_code, start_date=START_MONTHLY_TEST, end_date=TODAY)
            _check_df(df, f"月线 {ts_code} {name}")
        except Exception as e:
            global FAIL
            print(f"  ❌ 月线拉取异常 {ts_code}: {e}")
            FAIL += 1


def test_historical_data(pro):
    """测试历史 10 年日线数据拉取（仅取第一只股票避免频率限制）"""
    print("\n[6] 测试历史 10年 日线数据拉取（仅 000001.SZ）")
    symbol, market, name = TEST_SYMBOLS[0]
    ts_code = _ts_code(symbol, market)
    try:
        df = pro.daily(ts_code=ts_code, start_date=START_10Y, end_date=TODAY)
        _check_df(df, f"历史日线 {ts_code} {name}")
        if df is not None and not df.empty:
            print(f"    最早记录: {df.iloc[-1]['trade_date']}，最新记录: {df.iloc[0]['trade_date']}")
    except Exception as e:
        global FAIL
        print(f"  ❌ 历史日线拉取异常: {e}")
        FAIL += 1


def test_fetch_and_save_unit(pro):
    """模拟 _fetch_and_save 中的完整 Tushare 分支逻辑（不含 DB）"""
    print("\n[7] 模拟 _fetch_and_save Tushare 分支（不含 DB 写入）")
    symbol = "000001"
    period = "daily"
    start = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

    if symbol.startswith("6"):
        ts_code = f"{symbol}.SH"
    elif symbol.startswith("0") or symbol.startswith("3"):
        ts_code = f"{symbol}.SZ"
    elif symbol.startswith("4") or symbol.startswith("8"):
        ts_code = f"{symbol}.BJ"
    else:
        ts_code = symbol

    try:
        if period == "daily":
            df = pro.daily(ts_code=ts_code, start_date=start, end_date=TODAY)
        elif period == "weekly":
            df = pro.weekly(ts_code=ts_code, start_date=start, end_date=TODAY)
        elif period == "monthly":
            df = pro.monthly(ts_code=ts_code, start_date=start, end_date=TODAY)

        if df is not None and not df.empty:
            parsed = _check_data_format(df, f"完整模拟 {symbol} {period}")
            print(f"    → 解析后第一条: {parsed[0] if parsed else 'N/A'}")
        else:
            global FAIL
            print(f"  ❌ 模拟返回空数据")
            FAIL += 1
    except Exception as e:
        print(f"  ❌ 模拟 _fetch_and_save 异常: {e}")
        FAIL += 1


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def main():
    print("=" * 65)
    print("  Tushare 行情数据拉取测试 (market_price_tasks.py)")
    print(f"  日期: {TODAY}  服务器: {TUSHARE_HTTP_URL}")
    print("=" * 65)

    test_token_config()
    test_symbol_mapping()

    if not TUSHARE_TOKEN:
        print("\n❌ TUSHARE_TOKEN 未配置，跳过 API 测试")
        sys.exit(1)

    try:
        pro = _init_pro()
        print(f"\n  Tushare Pro 初始化成功 (url={TUSHARE_HTTP_URL})")
    except Exception as e:
        print(f"\n❌ Tushare 初始化失败: {e}")
        sys.exit(1)

    test_daily_data(pro)
    test_weekly_data(pro)
    test_monthly_data(pro)
    test_historical_data(pro)
    test_fetch_and_save_unit(pro)

    # 结果汇总
    total = PASS + FAIL
    print("\n" + "=" * 65)
    print(f"  测试完成: {PASS} 通过 / {FAIL} 失败 (共 {total})")
    print("=" * 65)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
