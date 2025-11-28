# main.py
import streamlit as st
from streamlit_option_menu import option_menu
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

# =======================
# 📊 初始化 session state
# =======================
if "last_analyzed_date" not in st.session_state:
    st.session_state["last_analyzed_date"] = None
if "rerun" not in st.session_state:
    st.session_state["rerun"] = False
if "analysis_type" not in st.session_state:
    st.session_state["analysis_type"] = "每日涨停投研分析"

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
# 📊 图表绘制函数
# =======================

def plot_concept_pie(raw_data: list):
    df = pd.DataFrame(raw_data)
    if '所属行业' in df.columns:
        top_concepts = df['所属行业'].value_counts().head(8)
    else:
        top_concepts = pd.Series(dtype='int64')

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
    if '连板数' in df.columns:
        df['连续涨停天数'] = pd.to_numeric(df['连板数'], errors='coerce').fillna(0).astype(int)
    else:
        df['连续涨停天数'] = 1

    if '首次封板时间' in df.columns:
        df['首次涨停时间'] = pd.to_datetime(df['首次封板时间'].astype(str).str.zfill(6), format='%H%M%S', errors='coerce')
    else:
        df['首次涨停时间'] = pd.NaT

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
    df['封单金额'] = pd.to_numeric(df['封板资金'], errors='coerce') / 1e8
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
    if CACHE_DIR is None:
        st.error("Agent 系统未正确加载，无法查看历史报告。")
        return
    report_path = CACHE_DIR / date / "report.md"
    if report_path.exists():
        content = report_path.read_text(encoding="utf-8")
        st.markdown("### 📄 查看历史报告")
        st.markdown(content)
    else:
        st.info("该日期暂无缓存报告。")

def show_opening_report(date: str):
    opening_cache_path = Path("cache/opening_analysis")
    report_path = opening_cache_path / date / "opening_analysis_report.md"
    if report_path.exists():
        content = report_path.read_text(encoding="utf-8")
        st.markdown("### 📊 开盘分析报告")
        st.markdown(content)
        st.caption(f"📅 分析日期: {date}")
    else:
        st.info("该日期暂无开盘分析报告。")

# =======================
# 🔍 自动加载最新缓存数据（用于显示可视化）
# =======================
def load_latest_cached_data():
    """加载最新的缓存数据用于可视化显示"""
    if CACHE_DIR is None or not CACHE_DIR.exists():
        return None

    all_cache_dirs = [d for d in CACHE_DIR.iterdir() if d.is_dir()]
    if not all_cache_dirs:
        return None

    latest_dir = max(all_cache_dirs, key=lambda x: x.name)
    state_file = latest_dir / "state.json"

    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"读取缓存数据失败: {e}")

    return None

# =======================
# 🏠 页面定义 - 首页 Dashboard
# =======================
def show_home_page():
    st.title("🏠 AI 涨停投研分析系统")

    col1, col2, col3 = st.columns(3)

    # 统计信息
    if CACHE_DIR and CACHE_DIR.exists():
        daily_reports = len([d for d in CACHE_DIR.iterdir() if d.is_dir()])
    else:
        daily_reports = 0

    opening_cache_path = Path("cache/opening_analysis")
    if opening_cache_path.exists():
        opening_reports = len([d for d in opening_cache_path.iterdir() if d.is_dir()])
    else:
        opening_reports = 0

    with col1:
        st.metric("📊 每日投研报告", daily_reports, delta="已缓存")
    with col2:
        st.metric("📈 开盘分析报告", opening_reports, delta="已生成")
    with col3:
        total_stocks = daily_reports * 20 if daily_reports else 0
        st.metric("🎯 分析股票总数", total_stocks, delta="估算")

    st.markdown("---")

    # 最新报告预览
    st.subheader("📄 最新报告预览")

    latest_cached = load_latest_cached_data()
    if latest_cached:
        st.info(f"📅 最新报告日期: {latest_cached.get('date', '未知')}")

        if "final_report" in latest_cached:
            report_preview = latest_cached["final_report"][:1000] + "..."
            st.markdown(report_preview)

            if st.button("📖 查看完整报告", key="view_latest_full"):
                st.markdown(latest_cached["final_report"])
    else:
        st.warning("暂无缓存报告，请先生成分析报告。")

    # 快速操作
    st.markdown("---")
    st.subheader("⚡ 快速操作")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 开始涨停分析", use_container_width=True):
            st.session_state["menu_option"] = "涨停分析"
            st.rerun()
    with col2:
        if st.button("📊 开始开盘分析", use_container_width=True):
            st.session_state["menu_option"] = "开盘分析"
            st.rerun()

# =======================
# 📈 页面定义 - 涨停分析
# =======================
def show_daily_analysis_page():
    st.title("📊 每日涨停投研分析")
    st.markdown("分析指定交易日的涨停股票，生成AI投研报告")

    # 日期输入
    default_date = datetime.now().strftime("%Y-%m-%d")
    date_input = st.text_input("📅 请输入分析日期（格式：YYYY-MM-DD）", value=default_date)
    analyze_button = st.button("🚀 开始涨停分析", type="primary")

    if analyze_button or st.session_state.get("rerun", False):
        # 如果rerun为True，重置它并执行强制重算
        if st.session_state.get("rerun", False):
            st.session_state["rerun"] = False
            force_rerun = True
            st.info("🔄 正在强制重算，忽略缓存...")
        else:
            force_rerun = False

        valid, msg = validate_date(date_input)
        if not valid:
            st.error(msg)
        else:
            with st.spinner(f"🔄 正在分析 {date_input} 的涨停股票数据..."):
                result = run_ai_research_analysis(date_input, force_rerun=force_rerun)

                if result["success"]:
                    final_state = result["result"]
                    cached = result.get("cached", False)

                    # 显示状态
                    if force_rerun:
                        # 强制重算成功
                        st.success(f"✅ 强制重算完成 · {date_input}")
                        st.toast("已重新生成报告，缓存已更新！", icon="✅")
                    elif cached:
                        # 使用缓存
                        st.info(f"📌 使用缓存结果 · {date_input}")
                        col1, col2 = st.columns([1, 6])
                        with col1:
                            if st.button("🔄 强制重算"):
                                st.session_state["rerun"] = True
                                st.rerun()
                    else:
                        # 新生成
                        st.success(f"✅ 成功生成新报告 · {date_input}")

                    # 显示报告内容
                    st.markdown("---")
                    st.subheader("🧠 AI 投研核心结论")

                    if "final_report" in final_state:
                        highlighted = highlight_and_render_md(final_state["final_report"])
                        st.markdown(f"<div style='line-height:1.8; font-size:16px;'>\n{highlighted}\n</div>", unsafe_allow_html=True)

                        # PDF导出
                        col_export, _ = st.columns([1, 5])
                        with col_export:
                            if st.button("📄 导出PDF报告"):
                                try:
                                    from report_export import ReportExporter
                                    exporter = ReportExporter()
                                    report_path = Path(CACHE_DIR) / date_input / "report.md"
                                    if report_path.exists():
                                        with st.spinner("正在生成PDF..."):
                                            pdf_path = exporter.markdown_to_pdf(str(report_path))
                                            if pdf_path:
                                                st.success(f"✅ PDF报告已生成: `{pdf_path}`")
                                                with open(pdf_path, 'rb') as f:
                                                    st.download_button(
                                                        label="⬇️ 下载PDF",
                                                        data=f,
                                                        file_name=f"涨停分析_{date_input}.pdf",
                                                        mime="application/pdf"
                                                    )
                                    else:
                                        st.warning("报告文件不存在")
                                except ImportError as e:
                                    st.error(f"PDF导出功能需要安装依赖: {e}\n请运行: `pip install reportlab`")
                                except Exception as e:
                                    st.error(f"导出失败: {e}")
                    else:
                        st.warning("未生成最终报告内容。")

                    # 数据可视化
                    raw_data = final_state.get("raw_limit_ups", [])
                    if raw_data:
                        st.markdown("---")
                        st.subheader("📊 数据可视化")

                        tab1, tab2, tab3 = st.tabs(["概念分布", "时间→连板流", "多维散点图"])

                        with tab1:
                            plot_concept_pie(raw_data)
                        with tab2:
                            plot_sankey_flow(raw_data)
                        with tab3:
                            plot_trend_over_time(raw_data)

                    st.session_state["last_analyzed_date"] = date_input

                else:
                    st.error("❌ 分析失败")
                    st.code(result["error"])
                    st.code(result.get("traceback", ""))

    # 显示历史缓存数据可视化（如果有）
    elif st.session_state.get("last_analyzed_date"):
        last_date = st.session_state["last_analyzed_date"]
        cache_path = Path(CACHE_DIR) / last_date / "state.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_state = json.load(f)

                raw_data = cached_state.get("raw_limit_ups", [])
                if raw_data:
                    st.markdown("---")
                    st.subheader("📊 最新缓存数据可视化")
                    st.info(f"📅 数据日期: {last_date}")

                    tab1, tab2, tab3 = st.tabs(["概念分布", "时间→连板流", "多维散点图"])

                    with tab1:
                        plot_concept_pie(raw_data)
                    with tab2:
                        plot_sankey_flow(raw_data)
                    with tab3:
                        plot_trend_over_time(raw_data)
            except Exception:
                pass

    # =======================
    # 📁 历史报告查看（添加到页面底部）
    # =======================
    st.markdown("---")
    st.subheader("📁 历史投研报告查看")

    # 获取历史报告列表
    if CACHE_DIR and CACHE_DIR.exists():
        daily_cache_dirs = sorted([d.name for d in CACHE_DIR.iterdir() if d.is_dir()], reverse=True)
    else:
        daily_cache_dirs = []

    if daily_cache_dirs:
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_hist_date = st.selectbox(
                "选择历史日期",
                options=daily_cache_dirs,
                index=0,
                help="选择要查看的历史报告日期"
            )
        with col2:
            if st.button("🔍 查看投研报告", key="view_daily_hist"):
                show_cached_report(selected_hist_date)
    else:
        st.info("暂无历史投研报告缓存")

    # =======================
    # 📤 批量导出功能
    # =======================
    st.markdown("---")
    st.subheader("📤 批量导出投研报告")

    col1, col2 = st.columns([1, 2])
    with col1:
        export_option = st.selectbox(
            "导出方式",
            options=["最近N个", "所有报告"],
            help="选择导出方式"
        )
    with col2:
        if export_option == "最近N个":
            n_reports = st.number_input("导出数量", min_value=1, max_value=20, value=3, key="daily_n_export")
            if st.button(f"📄 导出最近 {n_reports} 个报告", key="btn_daily_export"):
                try:
                    from report_export import export_reports
                    with st.spinner(f"正在导出最近 {n_reports} 个报告..."):
                        exported_files = export_reports(latest=n_reports, report_type="daily_research")
                        if exported_files:
                            st.success(f"✅ 成功导出 {len(exported_files)} 个报告")
                            st.info(f"文件保存在: `reports/pdf/` 目录")
                        else:
                            st.warning("没有找到可导出的报告")
                except ImportError:
                    st.error("请先安装依赖: `pip install reportlab`")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
        else:  # 所有报告
            if st.button("📄 导出所有投研报告", key="btn_daily_all"):
                try:
                    from report_export import export_reports
                    with st.spinner("正在导出所有每日投研报告..."):
                        exported_files = export_reports(all_reports=True, report_type="daily_research")
                        if exported_files:
                            st.success(f"✅ 成功导出 {len(exported_files)} 个报告")
                            st.info(f"文件保存在: `reports/pdf/` 目录")
                        else:
                            st.warning("没有找到可导出的报告")
                except ImportError:
                    st.error("请先安装依赖: `pip install reportlab`")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")

# =======================
# 🌅 页面定义 - 开盘分析
# =======================
def show_opening_analysis_page():
    st.title("🌅 开盘表现分析")
    st.markdown("追踪昨日涨停股票的今日开盘表现")

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    st.info(f"📊 将分析 **{yesterday}** 涨停股票今日开盘表现")
    analyze_button = st.button("🚀 开始开盘分析", type="primary")

    if analyze_button:
        with st.spinner(f"🔄 正在分析昨日涨停股票今日开盘表现..."):
            try:
                from opening_analysis_workflow import create_opening_analysis_workflow
                from opening_analysis_workflow import AnalysisState

                app = create_opening_analysis_workflow()

                initial_state: AnalysisState = {
                    'yesterday_report': None,
                    'limit_up_stocks': None,
                    'coach_recommended': None,
                    'today_opening_data': None,
                    'merged_data': None,
                    'coach_analysis': None,
                    'general_analysis': None,
                    'final_report': None,
                    'error': None
                }

                final_state = app.invoke(initial_state)

                if final_state.get('error'):
                    st.error(f"❌ 开盘分析执行失败: {final_state['error']}")
                else:
                    st.success(f"✅ 开盘分析完成！ ({yesterday} ➜ {today})")

                    st.markdown("---")
                    st.subheader("📊 开盘分析核心结论")

                    if "final_report" in final_state and final_state["final_report"]:
                        highlighted = highlight_and_render_md(final_state["final_report"])
                        st.markdown(f"<div style='line-height:1.8; font-size:16px;'>\n{highlighted}\n</div>", unsafe_allow_html=True)

                        # 保存到缓存
                        opening_cache_dir = Path("cache/opening_analysis") / today
                        opening_cache_dir.mkdir(parents=True, exist_ok=True)

                        report_file = opening_cache_dir / "opening_analysis_report.md"
                        with open(report_file, 'w', encoding='utf-8') as f:
                            f.write(final_state["final_report"])

                        state_file = opening_cache_dir / "state.json"
                        with open(state_file, 'w', encoding='utf-8') as f:
                            json.dump(final_state, f, ensure_ascii=False, indent=2)

                        # PDF导出
                        col_export, _ = st.columns([1, 5])
                        with col_export:
                            if st.button("📄 导出PDF报告"):
                                try:
                                    from report_export import ReportExporter
                                    exporter = ReportExporter()
                                    if report_file.exists():
                                        with st.spinner("正在生成PDF..."):
                                            pdf_path = exporter.markdown_to_pdf(str(report_file))
                                            if pdf_path:
                                                st.success(f"✅ PDF报告已生成: `{pdf_path}`")
                                                with open(pdf_path, 'rb') as f:
                                                    st.download_button(
                                                        label="⬇️ 下载PDF",
                                                        data=f,
                                                        file_name=f"开盘分析_{today}.pdf",
                                                        mime="application/pdf"
                                                    )
                                except ImportError as e:
                                    st.error(f"PDF导出功能需要安装依赖: {e}\n请运行: `pip install reportlab`")
                                except Exception as e:
                                    st.error(f"导出失败: {e}")

                        st.info("💾 开盘分析报告已缓存")
                    else:
                        st.warning("未生成开盘分析报告内容。")

            except ImportError as e:
                st.error(f"开盘分析模块导入失败: {e}")
                st.code("请确保 opening_analysis_workflow.py 文件存在且正确加载")
            except Exception as e:
                st.error(f"❌ 开盘分析执行异常: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    # =======================
    # 📁 历史开盘分析报告查看（添加到页面底部）
    # =======================
    st.markdown("---")
    st.subheader("📁 历史开盘分析报告查看")

    # 获取历史开盘分析报告列表
    opening_cache_path = Path("cache/opening_analysis")
    if opening_cache_path.exists():
        opening_cache_dirs = sorted([d.name for d in opening_cache_path.iterdir() if d.is_dir()], reverse=True)
    else:
        opening_cache_dirs = []

    if opening_cache_dirs:
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_opening_date = st.selectbox(
                "选择历史日期",
                options=opening_cache_dirs,
                index=0,
                help="选择要查看的历史开盘分析报告日期"
            )
        with col2:
            if st.button("🔍 查看开盘分析", key="view_opening_hist"):
                show_opening_report(selected_opening_date)
    else:
        st.info("暂无历史开盘分析报告缓存")

    # =======================
    # 📤 批量导出开盘分析
    # =======================
    st.markdown("---")
    st.subheader("📤 批量导出开盘分析")

    col1, col2 = st.columns([1, 2])
    with col1:
        export_option = st.selectbox(
            "导出方式",
            options=["最近N个", "所有开盘分析"],
            help="选择导出方式"
        )
    with col2:
        if export_option == "最近N个":
            n_reports = st.number_input("导出数量", min_value=1, max_value=20, value=3, key="opening_n_export")
            if st.button(f"📄 导出最近 {n_reports} 个开盘分析", key="btn_opening_export"):
                try:
                    from report_export import export_reports
                    with st.spinner(f"正在导出最近 {n_reports} 个开盘分析..."):
                        exported_files = export_reports(latest=n_reports, report_type="opening_analysis")
                        if exported_files:
                            st.success(f"✅ 成功导出 {len(exported_files)} 个报告")
                            st.info(f"文件保存在: `reports/pdf/` 目录")
                        else:
                            st.warning("没有找到可导出的报告")
                except ImportError:
                    st.error("请先安装依赖: `pip install reportlab`")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
        else:  # 所有开盘分析
            if st.button("📄 导出所有开盘分析", key="btn_opening_all"):
                try:
                    from report_export import export_reports
                    with st.spinner("正在导出所有开盘分析报告..."):
                        exported_files = export_reports(all_reports=True, report_type="opening_analysis")
                        if exported_files:
                            st.success(f"✅ 成功导出 {len(exported_files)} 个报告")
                            st.info(f"文件保存在: `reports/pdf/` 目录")
                        else:
                            st.warning("没有找到可导出的报告")
                except ImportError:
                    st.error("请先安装依赖: `pip install reportlab`")
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")

# =======================
# 🔄 简化侧边栏组件（只保留使用指南）
# =======================
def add_sidebar_components():
    """添加侧边栏组件（简化版，只保留使用指南）"""
    # 使用说明
    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ 使用指南"):
        st.markdown("""
        **🎯 功能说明：**

        **1️⃣ 每日涨停投研分析**
        - 分析指定日期的所有涨停股票
        - 生成AI投研报告（数据简报 + 策略师分析 + 操作建议）
        - 支持数据可视化（概念分布、时间流向、散点图）

        **2️⃣ 开盘表现分析**
        - 追踪昨日涨停股票的今日开盘表现
        - 分析连板率、涨停持续强度
        - 结合昨日短线龙头助手推荐进行深度分析

        **📊 使用方法：**
        - 选择页面菜单
        - 设置日期（开盘分析自动使用昨日日期）
        - 点击【开始分析】运行工作流
        - 查看报告、导出PDF或查看可视化图表

        **💾 历史记录：**
        - 所有报告自动缓存
        - 支持查看历史投研报告和开盘分析
        - 支持批量导出为PDF格式
        """)

# =======================
# 🧭 主程序 - 导航菜单
# =======================
def main():
    """主应用程序"""
    st.markdown("<style>\n    .css-1d391kg { padding-top: 0rem; }\n    .block-container { padding-top: 1rem; }\n</style>", unsafe_allow_html=True)

    with st.sidebar:
        st.title("RUO")
        selected = option_menu(
            menu_title=None,
            options=["首页", "涨停分析", "开盘分析"],
            icons=["house", "graph-up", "sunrise"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "black", "font-size": "16px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#02ab21"},
            }
        )

    # 添加侧边栏组件
    add_sidebar_components()

    # 根据选择显示对应页面
    if selected == "首页":
        show_home_page()
    elif selected == "涨停分析":
        show_daily_analysis_page()
    elif selected == "开盘分析":
        show_opening_analysis_page()

if __name__ == "__main__":
    main()
