from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # 先导入日志模块
    from src.core.logging import getLogger
    temp_logger = getLogger(__name__)
    temp_logger.warning("ReportLab未安装，PDF导出功能将不可用")

from src.core.logging import getLogger
logger = getLogger(__name__)


class PDFExporter:
    """PDF导出器类"""

    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chinese_font = "Helvetica"
        if REPORTLAB_AVAILABLE:
            self._register_fonts()
        logger.info("PDF导出器初始化完成")

    def _register_fonts(self):
        """注册中文字体"""
        try:
            # 尝试注册常见的中文字体
            font_paths = [
                # Windows系统字体路径
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
            ]

            font_registered = False
            for font_path in font_paths:
                try:
                    if Path(font_path).exists():
                        # 注册字体
                        pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                        # 映射字体
                        addMapping("ChineseFont", 0, 0, "ChineseFont")  # normal
                        addMapping("ChineseFont", 0, 1, "ChineseFont")  # italic
                        addMapping("ChineseFont", 1, 0, "ChineseFont")  # bold
                        addMapping("ChineseFont", 1, 1, "ChineseFont")  # bold italic
                        font_registered = True
                        logger.info(f"成功注册中文字体: {font_path}")
                        break
                except Exception as e:
                    logger.warning(f"注册字体失败 {font_path}: {e}")
                    continue

            if not font_registered:
                logger.warning("未找到可用的中文字体，PDF可能无法正确显示中文")
                self.chinese_font = "Helvetica"  # fallback to default
            else:
                self.chinese_font = "ChineseFont"

        except Exception as e:
            logger.error(f"字体注册失败: {e}")
            self.chinese_font = "Helvetica"

    def export_to_pdf(self, report_data, output_path=None):
        if not REPORTLAB_AVAILABLE:
            return {
                "success": False,
                "error": "ReportLab未安装，请先安装: pip install reportlab",
            }

        try:
            logger.info("开始导出PDF")

            if output_path is None:
                filename = f"{report_data['report_id']}.pdf"
                output_path = str(self.output_dir / filename)

            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
            )

            story = []
            styles = self._get_chinese_styles()

            self._add_title_section(story, styles, report_data)

            for section_name, content in report_data.get("sections", {}).items():
                self._add_section(story, styles, section_name, content)

            doc.build(story)

            logger.info(f"PDF导出成功: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "filename": Path(output_path).name,
            }

        except Exception as e:
            logger.error(f"PDF导出失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_chinese_styles(self):
        """获取支持中文的样式"""
        styles = getSampleStyleSheet()

        # 创建支持中文的样式
        styles.add(
            ParagraphStyle(
                name="ChineseTitle",
                fontName=self.chinese_font,
                fontSize=24,
                leading=28,
                alignment=TA_CENTER,
                spaceAfter=30,
            )
        )

        styles.add(
            ParagraphStyle(
                name="ChineseHeading",
                fontName=self.chinese_font,
                fontSize=16,
                leading=20,
                alignment=TA_LEFT,
                spaceBefore=20,
                spaceAfter=10,
            )
        )

        styles.add(
            ParagraphStyle(
                name="ChineseNormal",
                fontName=self.chinese_font,
                fontSize=12,
                leading=16,
                alignment=TA_LEFT,
                spaceAfter=10,
            )
        )

        return styles

    def _add_title_section(self, story, styles, report_data):
        """添加标题部分"""
        title = report_data.get("title", "安全评估报告")
        story.append(Paragraph(title, styles["ChineseTitle"]))
        story.append(Spacer(1, 12))

        meta_lines = [
            f"报告编号: {report_data.get('report_id', '')}",
            f"生成日期: {report_data.get('generate_date', datetime.now().strftime('%Y年%m月%d日'))}",
        ]

        if report_data.get("company"):
            meta_lines.append(f"公司名称: {report_data.get('company')}")

        for line in meta_lines:
            story.append(Paragraph(line, styles["ChineseNormal"]))

        story.append(Spacer(1, 20))

    def _add_section(self, story, styles, section_name, content):
        """添加章节内容"""
        story.append(Paragraph(section_name, styles["ChineseHeading"]))
        story.append(Paragraph(content, styles["ChineseNormal"]))
        story.append(Spacer(1, 10))
