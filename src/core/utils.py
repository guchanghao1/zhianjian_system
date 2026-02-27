"""
工具模块
包含文本处理、文件验证、路由等工具函数
"""

import re
import math
import os
import base64
from pathlib import Path

from langchain_core.documents import Document

from .config import DEFAULT_CONFIG
from .logging import getLogger

logger = getLogger(__name__)


class TextUtils:
    """文本处理工具类"""

    @staticmethod
    def clean_text(text):
        """清理文本，移除可能导致问题的字符"""
        if not text or not isinstance(text, str):
            return ""

        # 预编译正则表达式以提高性能
        if not hasattr(TextUtils, '_cleanup_patterns'):
            TextUtils._cleanup_patterns = [
                (re.compile(r"[\x00-\x1F\x7F-\x9F\u200B-\u200F\u202A-\u202E\u2060-\u206F\uFEFF]"), ""),
                (re.compile(r"\b(?:NaN|Infinity|INF)\b", re.IGNORECASE), ""),
                (re.compile(r"\s+"), " ")
            ]
        
        # 批量处理替换
        for pattern, replacement in TextUtils._cleanup_patterns:
            text = pattern.sub(replacement, text)
        
        return text.strip()

    @staticmethod
    def clean_nan_values(data):
        """清理数据中的NaN值，确保JSON序列化成功"""
        if data is None:
            return None
        
        if isinstance(data, dict):
            return {k: TextUtils.clean_nan_values(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [TextUtils.clean_nan_values(item) for item in data if item is not None]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                logger.debug(f"清理NaN/Inf值: {data}")
                return 0.0
            return data
        elif isinstance(data, str):
            # 清理字符串中的特殊值
            if data.lower() in ['nan', 'inf', '-inf', 'infinity', '-infinity']:
                logger.debug(f"清理字符串特殊值: {data}")
                return ""
            return data
        else:
            return data




class FileUtils:
    """文件处理工具类"""

    @staticmethod
    def validate_file(file_path, max_size=100 * 1024 * 1024):
        """验证文件类型和大小"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                return False
                
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                logger.warning(f"文件大小超出限制: {file_size} bytes > {max_size} bytes")
                return False

            # 检查文件类型
            allowed_extensions = {".pdf", ".txt", ".docx", ".doc"}
            ext = Path(file_path).suffix.lower()
            if ext not in allowed_extensions:
                logger.warning(f"不支持的文件类型: {ext}")
                return False
                
            logger.debug(f"文件验证通过: {file_path}")
            return True
        except OSError as e:
            logger.error(f"文件验证时发生系统错误: {e}")
            return False
        except Exception as e:
            logger.error(f"文件验证时发生未知错误: {e}")
            return False

    @staticmethod
    def validate_image(file_path):
        """验证图片文件"""
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                logger.warning(f"图片文件不存在: {file_path}")
                return False, "文件不存在"

            # 检查文件大小
            file_size = path.stat().st_size
            max_size = DEFAULT_CONFIG["max_image_size"]
            if file_size > max_size:
                logger.warning(f"图片文件过大: {file_size} bytes > {max_size} bytes")
                return False, f"文件大小超过限制 ({file_size / (1024*1024):.1f}MB > {max_size / (1024*1024):.1f}MB)"

            # 检查文件格式
            suffix = path.suffix.lower().lstrip(".")
            allowed_formats = DEFAULT_CONFIG["allowed_image_formats"]
            if suffix not in allowed_formats:
                logger.warning(f"不支持的图片格式: {suffix}, 支持格式: {allowed_formats}")
                return False, f"不支持的文件格式 ({suffix}), 请使用: {', '.join(allowed_formats)}"

            logger.debug(f"图片验证通过: {file_path}")
            return True, "验证通过"
        except OSError as e:
            logger.error(f"图片验证时发生系统错误: {e}")
            return False, f"系统错误: {str(e)}"
        except Exception as e:
            logger.error(f"图片验证时发生未知错误: {e}")
            return False, f"验证失败: {str(e)}"

    @staticmethod
    def load_file(file_path):
        """根据文件扩展名加载不同格式的文档"""
        ext = Path(file_path).suffix.lower()

        # 先尝试使用langchain的loader
        try:
            if ext == ".pdf":
                try:
                    from langchain_community.document_loaders import PyPDFLoader

                    return PyPDFLoader(file_path).load()
                except ImportError as e:
                    logger.error(f"PDF加载器导入失败: {e}")
                    raise
                except Exception as e:
                    logger.error(f"PDF文件加载失败: {e}")
                    raise
            elif ext in [".docx", ".doc"]:
                try:
                    from langchain_community.document_loaders import Docx2txtLoader

                    return Docx2txtLoader(file_path).load()
                except ImportError as e:
                    logger.error(f"DOCX加载器导入失败: {e}")
                    raise
                except Exception as e:
                    logger.error(f"DOCX文件加载失败: {e}")
                    raise
        except Exception as e:
            logger.error(f"文件加载失败: {e}")
            raise

        # 如果langchain loader不可用，使用基本文本加载
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return [Document(page_content=content, metadata={"source": str(path)})]
        except Exception as e:
            logger.error(f"文本文件加载失败: {e}")
            raise

    @staticmethod
    def image_to_base64(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def ensure_dir(dir_path):
        Path(dir_path).mkdir(parents=True, exist_ok=True)


class RoutingUtils:
    """问题路由工具类"""

    @staticmethod
    def route_question(question):
        """路由问题到相应的知识库集合"""
        if not question or not isinstance(question, str):
            logger.warning("无效的问题输入")
            return "safe"
        
        # 简单的关键词匹配路由
        question_lower = question.lower()
        if any(keyword in question_lower for keyword in ["安全", "隐患", "风险", "防护"]):
            return "safe"
        else:
            logger.debug(f"问题路由到默认集合: {question}")
            return "safe"  # 默认返回安全集合

    @staticmethod
    def extract_hazard_info(analysis_result):
        """从分析结果中提取危险信息用于检索"""
        if not analysis_result or not isinstance(analysis_result, dict):
            logger.warning("无效的分析结果输入")
            return "施工安全"
        
        hazards = analysis_result.get("hazards", [])
        if not hazards:
            return "施工安全"
        
        # 提取主要危险类型
        hazard_types = [hazard.get("hazard_type", "") for hazard in hazards if hazard.get("hazard_type")]
        if hazard_types:
            # 返回前几个危险类型的组合
            main_hazards = ", ".join(hazard_types[:3])
            logger.debug(f"提取的危险信息: {main_hazards}")
            return main_hazards
        
        return "施工安全"


class CacheUtils:
    """缓存工具类"""

    _cache = {}
    _max_size = 1000  # 最大缓存条目数

    @classmethod
    def get(cls, key):
        """获取缓存值"""
        return cls._cache.get(key)

    @classmethod
    def set(cls, key, value):
        """设置缓存值"""
        # 检查缓存大小，如果超限则清除最旧的条目
        if len(cls._cache) >= cls._max_size:
            # 删除第一个键值对（FIFO策略）
            oldest_key = next(iter(cls._cache))
            del cls._cache[oldest_key]
            logger.debug(f"缓存已满，删除最旧条目: {oldest_key}")
        
        cls._cache[key] = value
        logger.debug(f"缓存设置: {key}")

    @classmethod
    def clear(cls):
        """清空缓存"""
        cls._cache.clear()
        logger.info("缓存已清空")
        
    @classmethod
    def size(cls):
        """获取缓存大小"""
        return len(cls._cache)
        
    @classmethod
    def keys(cls):
        """获取所有缓存键"""
        return list(cls._cache.keys())
