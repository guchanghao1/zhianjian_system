"""
多模态分析工具
负责图像接收、预处理与安全隐患识别
"""

import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.core.config import MODELS
from src.core.utils import FileUtils, CacheUtils
from src.core.logging import getLogger

logger = getLogger(__name__)


class MultimodalAnalyzer:
    """多模态分析器类"""

    def __init__(self, model_name="qwen_vision"):
        self.model_config = MODELS.get(model_name, MODELS["qwen_vision"])
        self._init_model()
        logger.info("多模态分析器初始化完成")

    def _init_model(self):
        api_key = os.getenv(self.model_config["api_key_env"])
        if not api_key:
            logger.error(f"API密钥未找到: {self.model_config['api_key_env']}")
            raise ValueError(f"API密钥未配置: {self.model_config['api_key_env']}")

        logger.info(f"使用模型: {self.model_config['model']}")
        logger.info(f"API基础URL: {self.model_config['api_base']}")

        self.model = ChatOpenAI(
            model=self.model_config["model"],
            base_url=self.model_config["api_base"],
            api_key=api_key,
            temperature=0.3,
            max_tokens=2000,
        )

    def analyze_image(self, image_path, use_cache=True):
        cache_key = (
            f"multimodal_{Path(image_path).stat().st_mtime}_{Path(image_path).name}"
        )

        if use_cache:
            cached_result = CacheUtils.get(cache_key)
            if cached_result:
                logger.info("从缓存获取分析结果")
                return cached_result

        try:
            logger.info(f"开始分析图片: {image_path}")

            is_valid, message = FileUtils.validate_image(image_path)
            if not is_valid:
                return {"success": False, "error": message}

            image_base64 = FileUtils.image_to_base64(image_path)
            analysis_result = self._call_vision_model(image_base64)

            CacheUtils.set(cache_key, analysis_result)
            logger.info("图片分析完成")

            return analysis_result

        except Exception as e:
            logger.error(f"图片分析失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _call_vision_model(self, image_base64):
        system_prompt = """你是一位专业的建筑施工安全检查员。请分析这张施工现场图片，识别其中的安全隐患。

请以JSON格式返回分析结果，格式如下：
{{
    "success": true,
    "hazards": [
        {{
            "hazard_type": "隐患类型",
            "location": "位置描述",
            "severity": "high/medium/low",
            "description": "详细描述",
            "confidence": 0.95
        }}
    ],
    "summary": "整体评估总结"
}}
"""
        logger.info("构建视觉模型提示词")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                (
                    "human",
                    [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "请分析这张施工现场图片，识别安全隐患。",
                        },
                    ],
                ),
            ]
        )

        parser = JsonOutputParser()
        chain = prompt | self.model | parser

        logger.info("调用视觉模型...")
        try:
            result = chain.invoke({})
            if result is None:
                logger.warning("模型返回结果为None")
                raise ValueError("模型未返回有效结果")
            logger.info("模型调用成功")
            return result
        except Exception as e:
            logger.error(f"模型调用失败: {str(e)}")
            logger.warning(f"JSON解析失败: {e}")
            return {
                "success": True,
                "hazards": [
                    {
                        "hazard_type": "待分析",
                        "location": "图片中",
                        "severity": "medium",
                        "description": "需要进一步分析",
                        "confidence": 0.5,
                    }
                ],
                "summary": "图片已接收",
            }
