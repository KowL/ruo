"""
报告导出工具模块
支持将Markdown报告导出为PDF格式
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class ReportExporter:
    """报告导出器类"""

    def __init__(self):
        """初始化导出器"""
        if not PDF_SUPPORT:
            print("警告: reportlab 库未安装，PDF导出功能将不可用")
            print("请安装: pip install reportlab")

        self.cache_dir = Path("cache")
        self.export_dir = Path("reports/pdf")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def list_available_reports(self, report_type: str = "all") -> List[Dict]:
        """
        列出可用的报告

        Args:
            report_type: 报告类型 (daily_research, opening_analysis, all)

        Returns:
            报告列表，每个报告包含日期、类型、路径等信息
        """
        reports = []

        if report_type in ["daily_research", "all"]:
            daily_dir = self.cache_dir / "daily_research"
            if daily_dir.exists():
                for date_dir in sorted(daily_dir.iterdir(), reverse=True):
                    if date_dir.is_dir():
                        report_file = date_dir / "report.md"
                        if report_file.exists():
                            reports.append({
                                "date": date_dir.name,
                                "type": "每日投研报告",
                                "path": str(report_file),
                                "timestamp": datetime.strptime(date_dir.name, "%Y-%m-%d").timestamp()
                            })

        if report_type in ["opening_analysis", "all"]:
            opening_dir = self.cache_dir / "opening_analysis"
            if opening_dir.exists():
                for date_dir in sorted(opening_dir.iterdir(), reverse=True):
                    if date_dir.is_dir():
                        report_file = date_dir / "opening_analysis_report.md"
                        if report_file.exists():
                            reports.append({
                                "date": date_dir.name,
                                "type": "开盘分析报告",
                                "path": str(report_file),
                                "timestamp": datetime.strptime(date_dir.name, "%Y-%m-%d").timestamp()
                            })

        # 按日期排序（最新在前）
        reports.sort(key=lambda x: x["timestamp"], reverse=True)
        return reports

    def markdown_to_pdf(self, md_file: str, pdf_output: Optional[str] = None) -> str:
        """
        将Markdown文件转换为PDF

        Args:
            md_file: Markdown文件路径
            pdf_output: PDF输出路径（可选）

        Returns:
            PDF文件路径
        """
        if not PDF_SUPPORT:
            raise ImportError("reportlab 库未安装，无法导出PDF")

        # 读取Markdown文件
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 生成默认输出路径
        if pdf_output is None:
            md_path = Path(md_file)
            # 获取日期目录（父目录的名称）
            date_dir = md_path.parent.name
            # 根据路径判断报告类型
            if "daily_research" in str(md_path):
                report_type_name = "daily_research"
                base_name = "每日投研报告"
            elif "opening_analysis" in str(md_path):
                report_type_name = "opening_analysis"
                base_name = "开盘分析报告"
            elif "lhb" in str(md_path).lower():
                report_type_name = "lhb"
                base_name = "龙虎榜报告"
            else:
                report_type_name = "report"
                base_name = "分析报告"

            # 使用日期作为主文件名，避免重复覆盖
            pdf_output = str(self.export_dir / f"{base_name}_{date_dir}.pdf")

        # 创建PDF文档
        doc = SimpleDocTemplate(
            pdf_output,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )

        # 设置样式
        styles = getSampleStyleSheet()

        # 添加中文字体支持（如果系统中存在中文字体）
        try:
            # 尝试常见的中文字体路径
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
                "/Library/Fonts/Arial Unicode.ttf",     # macOS Arial Unicode
                "C:/Windows/Fonts/simsun.ttc",          # Windows 宋体
                "C:/Windows/Fonts/msyh.ttc"             # Windows 微软雅黑
            ]

            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Chinese', font_path))
                    # 更新样式以使用中文
                    styles['Normal'].fontName = 'Chinese'
                    styles['Heading1'].fontName = 'Chinese'
                    styles['Heading2'].fontName = 'Chinese'
                    styles['Heading3'].fontName = 'Chinese'
                    break
        except:
            pass  # 如果字体注册失败，使用默认字体

        # 解析Markdown并构建PDF内容
        story = []

        # 标题（尝试提取报告标题）
        lines = md_content.split('\n')
        title = "股票分析报告"
        for line in lines[:10]:
            if line.startswith('# ') and '今日涨停' in line:
                title = line.strip('# ').strip()
                break
            elif line.startswith('## 📋') or line.startswith('## 📊'):
                title = line.strip('# ').strip()
                break

        # 添加标题
        story.append(Paragraph(title, styles['Heading1']))
        story.append(Spacer(1, 12))

        # 添加日期信息
        date_info = Path(md_file).parent.parent.name
        story.append(Paragraph(f"报告日期: {date_info}", styles['Normal']))
        story.append(Spacer(1, 12))

        # 处理Markdown内容
        current_style = 'Normal'
        in_list = False

        for line in lines:
            line = line.rstrip()

            # 空行
            if not line:
                story.append(Spacer(1, 6))
                continue

            # 标题
            if line.startswith('# '):
                story.append(Paragraph(line.strip('# '), styles['Heading1']))
                story.append(Spacer(1, 6))
            elif line.startswith('## '):
                story.append(Paragraph(line.strip('# '), styles['Heading2']))
                story.append(Spacer(1, 6))
            elif line.startswith('### '):
                story.append(Paragraph(line.strip('# '), styles['Heading3']))
                story.append(Spacer(1, 6))

            # 重要提示块（以'>'开头的引用）
            elif line.startswith('> '):
                quote_text = line.strip('> ')
                # 使用不同的样式来突出显示
                quote_style = ParagraphStyle(
                    'Quote',
                    parent=styles['Normal'],
                    leftIndent=20,
                    rightIndent=20,
                    spaceBefore=6,
                    spaceAfter=6,
                    backColor=colors.lightgrey
                )
                story.append(Paragraph(quote_text, quote_style))

            # 列表项
            elif line.startswith('- ') or line.startswith('* ') or line.startswith('+ '):
                list_text = line.strip('-*+ ')
                story.append(Paragraph(f'• {list_text}', styles['Normal']))

            # 加粗文本（简单处理）
            elif '**' in line:
                # 替换**为粗体（PDF中使用不同字体或下划线模拟）
                line = line.replace('**', '')
                story.append(Paragraph(line, styles['Normal']))

            # 普通段落
            else:
                story.append(Paragraph(line, styles['Normal']))

        # 构建PDF
        doc.build(story)

        print(f"✓ PDF报告已生成: {pdf_output}")
        return pdf_output

    def export_by_date(self, date: str, report_type: str = "all") -> List[str]:
        """
        按日期导出报告

        Args:
            date: 日期字符串 (YYYY-MM-DD)
            report_type: 报告类型

        Returns:
            导出的PDF文件路径列表
        """
        reports = self.list_available_reports(report_type)
        exported_files = []

        for report in reports:
            if report["date"] == date:
                try:
                    pdf_path = self.markdown_to_pdf(report["path"])
                    exported_files.append(pdf_path)
                except Exception as e:
                    print(f"✗ 导出失败 ({report['date']} - {report['type']}): {e}")

        return exported_files

    def export_latest(self, n: int = 1, report_type: str = "all") -> List[str]:
        """
        导出最新的n个报告

        Args:
            n: 导出数量
            report_type: 报告类型

        Returns:
            导出的PDF文件路径列表
        """
        reports = self.list_available_reports(report_type)
        exported_files = []

        for i, report in enumerate(reports[:n]):
            try:
                print(f"[{i+1}/{n}] 导出报告: {report['date']} ({report['type']})")
                pdf_path = self.markdown_to_pdf(report["path"])
                exported_files.append(pdf_path)
            except Exception as e:
                print(f"✗ 导出失败 ({report['date']} - {report['type']}): {e}")

        return exported_files

    def export_all(self, report_type: str = "all") -> List[str]:
        """
        导出所有报告

        Args:
            report_type: 报告类型

        Returns:
            导出的PDF文件路径列表
        """
        reports = self.list_available_reports(report_type)
        print(f"共找到 {len(reports)} 个报告")

        exported_files = []
        for i, report in enumerate(reports):
            try:
                print(f"[{i+1}/{len(reports)}] 导出报告: {report['date']} ({report['type']})")
                pdf_path = self.markdown_to_pdf(report["path"])
                exported_files.append(pdf_path)
            except Exception as e:
                print(f"✗ 导出失败 ({report['date']} - {report['type']}): {e}")

        return exported_files


def export_reports(
    date: Optional[str] = None,
    latest: Optional[int] = None,
    report_type: str = "all",
    all_reports: bool = False
) -> List[str]:
    """
    导出报告的主函数

    Args:
        date: 指定日期导出 (YYYY-MM-DD)
        latest: 导出最近N个报告
        report_type: 报告类型 (daily_research, opening_analysis, all)
        all_reports: 是否导出所有报告

    Returns:
        导出的PDF文件路径列表
    """
    exporter = ReportExporter()

    if all_reports:
        return exporter.export_all(report_type)
    elif date:
        return exporter.export_by_date(date, report_type)
    elif latest:
        return exporter.export_latest(latest, report_type)
    else:
        # 默认导出最新的1个
        return exporter.export_latest(1, report_type)


if __name__ == "__main__":
    # 测试导出功能
    print("=" * 50)
    print("股票分析报告导出工具")
    print("=" * 50)

    # 示例：导出最新的3个报告
    print("\n[示例] 导出最新的3个报告:")
    try:
        exported = export_reports(latest=3, report_type="all")
        print(f"\n成功导出 {len(exported)} 个报告:")
        for pdf_path in exported:
            print(f"  - {pdf_path}")
    except ImportError as e:
        print(f"错误: {e}")
