"""
报告生成工具
实现结构化报告模板管理与动态内容填充
"""

import os
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.core.config import MODELS, REPORT_TEMPLATE, RISK_LEVELS
from src.core.utils import CacheUtils
from src.core.logging import getLogger

logger = getLogger(__name__)


class ReportGenerator:
    """报告生成器类"""

    def __init__(self, model_name="qwen"):
        self.model_config = MODELS.get(model_name, MODELS["qwen"])
        self.report_template = REPORT_TEMPLATE
        self._init_model()
        logger.info("报告生成器初始化完成")

    def _init_model(self):
        api_key = os.getenv(self.model_config["api_key_env"])
        self.model = ChatOpenAI(
            model=self.model_config["model"],
            base_url=self.model_config["api_base"],
            api_key=api_key,
            temperature=0.3,
            max_tokens=3000,
        )

    def generate_report(self, analysis_result, retrieved_docs, metadata=None):
        try:
            logger.info("开始生成安全评估报告")

            if metadata is None:
                metadata = {}

            report_id = f"REPORT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            report_data = {
                "report_id": report_id,
                "title": metadata.get("title", self.report_template["title"]),
                "company": metadata.get("company", ""),
                "generate_date": metadata.get(
                    "date", datetime.now().strftime("%Y年%m月%d日")
                ),
                "sections": {},
            }

            hazards = analysis_result.get("hazards", [])
            if not hazards:
                report_data["sections"]["隐患概述"] = "未检测到明显安全隐患"
                report_data["overall_risk"] = "low"
            else:
                overall_risk = self._calculate_overall_risk(hazards)
                report_data["overall_risk"] = overall_risk

                for section in self.report_template["sections"]:
                    content = self._generate_section_content(
                        section, analysis_result, retrieved_docs
                    )
                    report_data["sections"][section] = content

            logger.info("报告生成完成")
            return report_data

        except Exception as e:
            logger.error(f"报告生成失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _calculate_overall_risk(self, hazards):
        risk_scores = {"high": 3, "medium": 2, "low": 1}
        total_score = 0

        for hazard in hazards:
            severity = hazard.get("severity", "low")
            total_score += risk_scores.get(severity, 1)

        avg_score = total_score / len(hazards) if hazards else 0

        if avg_score >= 2.5:
            return "high"
        elif avg_score >= 1.5:
            return "medium"
        else:
            return "low"

    def _generate_section_content(self, section_name, analysis_result, retrieved_docs):
        cache_key = f"report_section_{hash(section_name)}_{hash(str(analysis_result))}"
        cached_content = CacheUtils.get(cache_key)
        if cached_content:
            return cached_content

        hazards = analysis_result.get("hazards", [])
        summary = analysis_result.get("summary", "")

        prompt_template = self._get_section_prompt(section_name)

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.model | StrOutputParser()

        try:
            content = chain.invoke({"hazards": hazards, "summary": summary})

            CacheUtils.set(cache_key, content)
            return content
        except Exception as e:
            logger.warning(f"生成章节 {section_name} 失败: {e}")
            return f"{section_name}生成失败"

    def _get_section_prompt(self, section_name):
        prompts = {
            "隐患概述": "请根据以下隐患信息，生成简洁的隐患概述，不超过300字。\n\n隐患信息：{hazards}",
            "风险等级评估": "请根据以下隐患信息，进行风险等级评估。\n\n隐患列表：{hazards}",
            "隐患详细描述": "请详细描述以下安全隐患。\n\n隐患信息：{hazards}",
            "整改建议": "请根据以下隐患信息，提出整改建议。\n\n隐患信息：{hazards}",
            "预防措施": "请根据以下隐患信息，提出预防措施。\n\n隐患信息：{hazards}",
            "相关法规依据": "请列出与以下隐患相关的建筑施工安全法规。\n\n隐患信息：{hazards}",
        }
        return prompts.get(section_name, "请根据以下信息生成内容：\n{hazards}")

    def format_report_for_display(self, report_data):
        if report_data.get("success") is False:
            return f"报告生成失败：{report_data.get('error', '未知错误')}"

        output = [
            f"# {report_data['title']}",
            f"**报告编号**：{report_data['report_id']}",
            f"**生成日期**：{report_data['generate_date']}",
        ]

        if report_data.get("company"):
            output.append(f"**公司名称**：{report_data['company']}")

        overall_risk = report_data.get("overall_risk", "low")
        risk_info = RISK_LEVELS.get(overall_risk, RISK_LEVELS["low"])
        output.append(f"\n## 整体风险评估：{risk_info['label']}")

        for section_name, content in report_data.get("sections", {}).items():
            output.append(f"\n## {section_name}")
            output.append(content)

        return "\n".join(output)
