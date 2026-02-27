"""
配置文件
包含模型配置、默认参数、路径设置等
"""

from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.parent

# 默认配置
DEFAULT_CONFIG = {
    "persist_dir": str(BASE_DIR / "data" / "chroma_db"),
    "upload_dir": str(BASE_DIR / "data" / "uploads"),
    "embedding_model": "bge-m3:latest",
    "chunk_size": 400,
    "chunk_overlap": 40,
    "retrieval_k": 5,
    "max_image_size": 10 * 1024 * 1024,
    "allowed_image_formats": ["jpg", "jpeg", "png"],
}

# 模型配置
MODELS = {
    "qwen": {
        "model": "qwen3-max-2025-09-23",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
    "qwen_vision": {
        "model": "qwen-vl-plus",  # 改为专门的视觉模型
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
}

# 风险等级配置
RISK_LEVELS = {
    "high": {"label": "高风险", "color": "#FF0000", "description": "立即整改"},
    "medium": {"label": "中风险", "color": "#FFA500", "description": "限期整改"},
    "low": {"label": "低风险", "color": "#FFFF00", "description": "注意防范"},
}

# 报告模板配置
REPORT_TEMPLATE = {
    "title": "施工现场安全评估报告",
    "sections": [
        "隐患概述",
        "风险等级评估",
        "隐患详细描述",
        "整改建议",
        "预防措施",
        "相关法规依据",
    ],
}
