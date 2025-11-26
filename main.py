# main.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from pathlib import Path
import json
import traceback

# 导入自定义 Agent 系统
try:
    from agent_system import run_ai_research_analysis, is_cached, CACHE_DIR
except ImportError as e:
    st.error(f"无法加载 agent_system: {e}")
    st.code(traceback.format_exc())
    st.stop()

# =======================
# 🎨 页面配置
# =======================
st.set_page_config(
    page_title="AI 涨停投研分析系统",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI 涨停投研分析系统")
st.markdown("基于 **LangGraph 多 Agent 工作流 + 通义千问 + AkShare 实时数据**")

# =======================
# 📅 日期选择器
# =======================
default_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
date_input = st.text_input("请输入分析日期（格式：YYYY-MM-DD）", value=default_date)
analyze_button = st.button("开始分析", type="primary")

# 初始化 session state
if "last_analyzed_date" not in st.session_state:
    st.session_state["last_analyzed_date"] = None
if "rerun" not in st.session_state:
    st.session_state["rerun"] = False

# 清除重跑标志
def reset_rerun():
    st.session_state["rerun"] = False

# =======================
# 🔍 日期合法性校验
# =======================
def validate_date(date_str: str) -> tuple[bool, str]:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.weekday() >= 5:  # 周六日
            return False, "所选日期为周末，非交易日。"
        if dt.date() > datetime.now().date():
            return False, "不能分析未来日期。"
        return True, ""
    except ValueError:
        return False, "日期格式错误，请使用 YYYY-MM-DD。"

# =======================
# 🖍️ 高亮渲染函数（增强可读性）
# =======================
def highlight_and_render_md(text: str) -> str:
    """对关键信息进行 HTML 高亮处理"""
    if not isinstance(text, str):
        return str(text)
    
    text = text.replace("✅", "<span style='color:green;'>✅</span>")
    text = text.replace("⚠️", "<span style='color:orange;'>⚠️</span>")
    text = text.replace("🎯", "<span style='color:#ff6b6b;'>🎯</span>")
    text = text.replace("💡", "<span style='color:blue;'>💡</span>")
    text = text.replace("🛡️", "<span style='color:gold;'>🛡️</span>")
    text = text.replace("🥋", "<span style='color:#a0522d;'>🥋</span>")
    text = text.replace("**", "<strong>").replace("</strong><strong>", "")
    return text

# =======================
# 📊 图表绘制函数
# =======================

def plot_concept_pie(raw_data: list):
    df = pd.DataFrame(raw_data)
    concepts_series = df['概念'].str.split(',').explode().str.strip()
    top_concepts = concepts_series.value_counts().head(8)
    
    fig = px.pie(
        values=top_concepts.values,
        names=top_concepts.index,
        title="🔥 涨停股热点概念分布",
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    fig.update_traces(textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

def plot_sankey_flow(raw_data: list):
    df = pd.DataFrame(raw_data)
    df['连续涨停天数'] = pd.to_numeric(df['连续涨停天数'], errors='coerce').fillna(0).astype(int)
    df['首次涨停时间'] = pd.to_datetime(df['首次涨停时间'], errors='coerce')
    df['时间段'] = df['首次涨停时间'].dt.hour.apply(
        lambda x: '早盘' if x < 10 else '中盘' if x < 14 else '尾盘'
    )
    df['连板类型'] = df['连续涨停天数'].apply(
        lambda x: '首板' if x <= 1 else f'{x}连板'
    )

    source = []
    target = []
    value = []

    time_to_id = {"早盘": 0, "中盘": 1, "尾盘": 2}
    lianban_to_id = {"首板": 3, "2连板": 4, "3连板": 5, "4连板": 6, "5连板及以上": 7}

    for _, row in df.iterrows():
        time_slot = row['时间段']
        lianban_label = row['连板类型'] if row['连续涨停天数'] < 5 else "5连板及以上"
        
        src_idx = time_to_id.get(time_slot, -1)
        tgt_idx = lianban_to_id.get(lianban_label, -1)
        if src_idx != -1 and tgt_idx != -1:
            source.append(src_idx)
            target.append(tgt_idx)
            value.append(1)

    label_list = ["早盘", "中盘", "尾盘", "首板", "2连板", "3连板", "4连板", "5连板及以上"]
    color_list = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880"]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=label_list,
            color=color_list
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color="rgba(128,128,128,0.2)"
        )
    )])
    fig.update_layout(title_text="⏳ 涨停时间 → 连板强度流向图", font_size=12)
    st.plotly_chart(fig, use_container_width=True)

def plot_trend_over_time(raw_data: list):
    df = pd.DataFrame(raw_data)
    df['封单金额'] = pd.to_numeric(df['封单资金'], errors='coerce') / 1e8  # 单位：亿元
    df['换手率'] = pd.to_numeric(df['换手率'], errors='coerce')

    fig = px.scatter(
        df,
        x='换手率',
        y='封单金额',
        size='流通市值', size_max=30,
        color='涨跌幅',
        color_continuous_scale='RdYlGn',
        hover_name='名称',
        title="📊 换手率 vs 封单金额（气泡大小=流通市值）",
        labels={'封单金额': '封单金额（亿元）', '换手率': '换手率(%)'}
    )
    st.plotly_chart(fig, use_container_width=True)

# =======================
# 🗂️ 缓存报告查看功能
# =======================
def show_cached_report(date: str):
    report_path = CACHE_DIR / date / "report.md"
    if report_path.exists():
        content = report_path.read_text(encoding="utf-8")
        st.markdown("### 📄 查看历史报告")
        st.markdown(content)
    else:
        st.info("该日期暂无缓存报告。")

# =======================
# 🧩 主执行逻辑
# =======================
if analyze_button:
    valid, msg = validate_date(date_input)
    if not valid:
        st.error(msg)
    else:
        with st.spinner(f"正在分析 {date_input} 的市场数据..."):
            result = run_ai_research_analysis(date_input, force_rerun=st.session_state.get("rerun", False))

            if result["success"]:
                final_state = result["result"]
                cached = result.get("cached", False)

                # 显示状态提示
                if cached:
                    st.info(f"📌 使用缓存结果 · {date_input}")
                    col1, col2 = st.columns([1, 6])
                    with col1:
                        if st.button("🔄 强制重算", on_click=lambda: st.session_state.update(rerun=True)):
                            pass
                else:
                    st.success(f"✅ 成功生成新报告 · {date_input}")

                # =======================
                # 📝 显示 AI 分析报告
                # =======================
                st.subheader("🧠 AI 投研核心结论")
                if "final_report" in final_state:
                    highlighted = highlight_and_render_md(final_state["final_report"])
                    st.markdown(f"<div style='line-height:1.8; font-size:16px;'>{highlighted}</div>", unsafe_allow_html=True)
                else:
                    st.warning("未生成最终报告内容。")

                # =======================
                # 📈 数据可视化区域
                # =======================
                raw_data = final_state.get("raw_limit_ups", [])
                if raw_data:
                    st.subheader("📊 数据可视化")

                    tab1, tab2, tab3 = st.tabs(["概念分布", "时间→连板流", "多维散点图"])

                    with tab1:
                        plot_concept_pie(raw_data)

                    with tab2:
                        plot_sankey_flow(raw_data)

                    with tab3:
                        plot_trend_over_time(raw_data)

                # 更新最后分析日期
                st.session_state["last_analyzed_date"] = date_input

            else:
                st.error("❌ 分析失败")
                st.code(result["error"])
                st.code(result.get("traceback", ""))

# =======================
# 🗃️ 历史报告管理侧边栏
# =======================
st.sidebar.title("📁 历史报告")
all_cache_dirs = [d.name for d in CACHE_DIR.iterdir() if d.is_dir()]
selected_hist_date = st.sidebar.selectbox("选择历史日期", options=all_cache_dirs, index=0) if all_cache_dirs else None

if selected_hist_date:
    if st.sidebar.button("🔍 查看报告"):
        show_cached_report(selected_hist_date)

# 显示所有可用缓存
if all_cache_dirs:
    st.sidebar.markdown("---")
    st.sidebar.write("📅 已缓存日期：")
    for d in sorted(all_cache_dirs, reverse=True)[:10]:
        st.sidebar.caption(d)
else:
    st.sidebar.info("暂无缓存报告")

# =======================
# 💡 提示信息
# =======================
with st.sidebar.expander("ℹ️ 使用说明"):
    st.markdown("""
    - 输入一个交易日（如 `2025-04-05`）
    - 点击【开始分析】将启动多 Agent 工作流
    - 若存在缓存则直接读取，否则实时调用 Qwen 分析
    - 支持后续扩展：微信推送 / 自动回测 / RAG 查询
    """)
