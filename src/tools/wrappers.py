import json
from pathlib import Path

from src.tools import (
    MultimodalAnalyzer,
    KnowledgeRetriever,
    ReportGenerator,
    PDFExporter,
)
from src.core.logging import getLogger

logger = getLogger(__name__)


class ErrorCode:
    SUCCESS = "0000"
    INVALID_INPUT = "1001"
    FILE_NOT_FOUND = "1002"
    INVALID_FILE_FORMAT = "1003"
    FILE_SIZE_EXCEEDED = "1004"
    TOOL_EXECUTION_ERROR = "2001"
    NETWORK_ERROR = "2002"
    INTERNAL_ERROR = "9999"


class ErrorMessage:
    MESSAGES = {
        ErrorCode.SUCCESS: "操作成功",
        ErrorCode.INVALID_INPUT: "输入参数无效",
        ErrorCode.FILE_NOT_FOUND: "文件不存在",
        ErrorCode.INVALID_FILE_FORMAT: "无效的文件格式",
        ErrorCode.FILE_SIZE_EXCEEDED: "文件大小超出限制",
        ErrorCode.TOOL_EXECUTION_ERROR: "工具执行错误",
        ErrorCode.NETWORK_ERROR: "网络错误",
        ErrorCode.INTERNAL_ERROR: "内部错误",
    }


class Validator:
    @staticmethod
    def validate_required(value, field_name):
        """验证必填字段"""
        if value is None:
            return False, f"{field_name} 不能为空"
        if isinstance(value, str) and not value.strip():
            return False, f"{field_name} 不能为空"
        return True, None

    @staticmethod
    def validate_file_exists(file_path):
        """验证文件是否存在"""
        if not file_path or not isinstance(file_path, str):
            return False, "文件路径无效"
        
        try:
            path = Path(file_path)
            if not path.exists():
                return False, ErrorMessage.MESSAGES[ErrorCode.FILE_NOT_FOUND]
            if not path.is_file():
                return False, "指定路径不是文件"
            return True, None
        except Exception as e:
            return False, f"文件检查失败: {str(e)}"

    @staticmethod
    def validate_image_format(file_path):
        """验证图片格式"""
        if not file_path or not isinstance(file_path, str):
            return False, "文件路径无效"
            
        allowed_formats = [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]
        try:
            path = Path(file_path)
            suffix = path.suffix
            if not suffix:
                return False, "文件没有扩展名"
            if suffix not in allowed_formats:
                return False, f"{ErrorMessage.MESSAGES[ErrorCode.INVALID_FILE_FORMAT]} (支持格式: {', '.join(allowed_formats)})"
            return True, None
        except Exception as e:
            return False, f"格式检查失败: {str(e)}"

    @staticmethod
    def validate_json(input_str):
        """验证JSON格式"""
        if not input_str or not isinstance(input_str, str):
            return False, None
        
        try:
            data = json.loads(input_str)
            if not isinstance(data, dict):
                return False, None
            return True, data
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
            return False, None
        except Exception as e:
            logger.error(f"JSON验证异常: {e}")
            return False, None


# 初始化全局工具实例
try:
    multimodal_analyzer = MultimodalAnalyzer()
    knowledge_retriever = KnowledgeRetriever()
    report_generator = ReportGenerator()
    pdf_exporter = PDFExporter()
    logger.info("所有工具初始化成功")
except Exception as e:
    logger.error(f"工具初始化失败: {e}")
    raise


def analyze_image_tool(input_str):
    """分析施工现场图片，识别安全隐患。输入应为图片文件路径。"""
    try:
        # 输入验证
        is_valid, error_msg = Validator.validate_required(input_str, "图片路径")
        if not is_valid:
            logger.warning(f"输入验证失败: {error_msg}")
            return f"[{ErrorCode.INVALID_INPUT}] {error_msg}"

        image_path = input_str.strip()
        
        # 文件存在性检查
        is_valid, error_msg = Validator.validate_file_exists(image_path)
        if not is_valid:
            logger.warning(f"文件不存在: {image_path}")
            return f"[{ErrorCode.FILE_NOT_FOUND}] {error_msg}: {image_path}"

        # 文件格式检查
        is_valid, error_msg = Validator.validate_image_format(image_path)
        if not is_valid:
            logger.warning(f"文件格式不支持: {image_path}")
            return f"[{ErrorCode.INVALID_FILE_FORMAT}] {error_msg}"

        # 执行分析
        logger.info(f"开始分析图片: {image_path}")
        result = multimodal_analyzer.analyze_image(image_path)

        if result.get("success"):
            hazards = result.get("hazards", [])
            summary = result.get("summary", "")
            
            # 构建响应输出
            output = f"分析完成！\n\n{summary}\n\n"

            if hazards:
                output += "检测到的隐患：\n"
                for i, hazard in enumerate(hazards, 1):
                    hazard_type = hazard.get('hazard_type', '未知')
                    severity = hazard.get('severity', 'low')
                    location = hazard.get('location', '未知')
                    description = hazard.get('description', '')
                    
                    output += f"{i}. {hazard_type} - {severity}\n"
                    output += f"   位置: {location}\n"
                    output += f"   描述: {description}\n"
            else:
                output += "未检测到明显安全隐患"

            logger.info(f"图片分析完成，检测到 {len(hazards)} 个隐患")
            return output
        else:
            error_detail = result.get('error', '未知错误')
            logger.error(f"图片分析失败: {error_detail}")
            return f"[{ErrorCode.TOOL_EXECUTION_ERROR}] 分析失败: {error_detail}"
            
    except Exception as e:
        logger.error(f"工具调用异常: {e}", exc_info=True)
        return f"[{ErrorCode.INTERNAL_ERROR}] 工具调用出错: {str(e)}"


def retrieve_knowledge_tool(query):
    """从知识库中检索相关的建筑施工安全知识。输入为查询关键词。"""
    try:
        is_valid, error_msg = Validator.validate_required(query, "查询关键词")
        if not is_valid:
            return f"[{ErrorCode.INVALID_INPUT}] {error_msg}"

        results = knowledge_retriever.retrieve(query, "safe")

        if results:
            output = f'关于"{query}"，从知识库中检索到相关知识如下：\n\n'
            for i, doc in enumerate(results, 1):
                content = doc.page_content
                content = content.replace("### ", "").replace("## ", "")
                content = "\n".join([line for line in content.split("\n") if line.strip()])
                output += f"{i}. {content}\n\n"
            output += "如需进一步了解某一方面的详细内容，可继续提问。"
            return output
        else:
            return "未检索到相关知识"
    except Exception as e:
        return f"[{ErrorCode.INTERNAL_ERROR}] 工具调用出错: {str(e)}"


def generate_report_tool(input_str):
    """生成安全评估报告。输入应为JSON格式的分析结果，或使用默认示例数据。"""
    try:
        from datetime import datetime

        analysis_result = {
            "success": True,
            "hazards": [
                {
                    "hazard_type": "未佩戴安全帽",
                    "location": "图片左侧工人",
                    "severity": "high",
                    "description": "工人未按规定佩戴安全帽",
                    "confidence": 0.95,
                }
            ],
            "summary": "检测到1项高风险隐患",
        }

        if input_str.strip():
            is_valid, parsed_data = Validator.validate_json(input_str)
            if is_valid and "hazards" in parsed_data:
                analysis_result = parsed_data

        retrieved_docs = knowledge_retriever.retrieve("施工安全", "safe")

        metadata = {
            "title": "施工现场安全评估报告",
            "date": datetime.now().strftime("%Y年%m月%d日"),
        }

        report_data = report_generator.generate_report(
            analysis_result, retrieved_docs, metadata
        )

        if report_data.get("success") is False:
            return f"[{ErrorCode.TOOL_EXECUTION_ERROR}] 报告生成失败: {report_data.get('error')}"

        formatted_report = report_generator.format_report_for_display(report_data)
        return formatted_report
    except Exception as e:
        return f"[{ErrorCode.INTERNAL_ERROR}] 工具调用出错: {str(e)}"


def export_pdf_tool(input_str):
    """导出PDF报告。输入为报告标题，将生成示例PDF报告。"""
    try:
        from datetime import datetime

        analysis_result = {
            "success": True,
            "hazards": [
                {
                    "hazard_type": "示例隐患",
                    "location": "示例位置",
                    "severity": "medium",
                    "description": "这是一个示例报告",
                    "confidence": 0.9,
                }
            ],
            "summary": "示例报告",
        }

        retrieved_docs = []

        report_title = input_str.strip() if input_str.strip() else "安全评估报告"
        metadata = {
            "title": report_title,
            "date": datetime.now().strftime("%Y年%m月%d日"),
        }

        report_data = report_generator.generate_report(
            analysis_result, retrieved_docs, metadata
        )

        if report_data.get("success") is False:
            return f"[{ErrorCode.TOOL_EXECUTION_ERROR}] 报告生成失败: {report_data.get('error')}"

        pdf_result = pdf_exporter.export_to_pdf(report_data)

        if pdf_result.get("success"):
            return f"[{ErrorCode.SUCCESS}] PDF导出成功！文件保存至: {pdf_result.get('output_path')}"
        else:
            return f"[{ErrorCode.TOOL_EXECUTION_ERROR}] PDF导出失败: {pdf_result.get('error')}"
    except Exception as e:
        return f"[{ErrorCode.INTERNAL_ERROR}] 工具调用出错: {str(e)}"
