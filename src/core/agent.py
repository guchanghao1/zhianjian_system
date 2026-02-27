import os
import re
import time
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, AgentMiddleware
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langgraph.checkpoint.memory import InMemorySaver

from src.tools import (
    analyze_image_tool,
    retrieve_knowledge_tool,
    generate_report_tool,
    export_pdf_tool,
)
from src.core.logging import getLogger

logger = getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取API配置
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL")

if not api_key or not base_url:
    logger.error("API配置缺失，请检查.env文件")
    raise ValueError("API密钥或基础URL未配置")

model = ChatOpenAI(
    model="qwen3-max-2025-09-23",
    api_key=api_key,
    base_url=base_url,
    temperature=0.3,
)

system_prompt = """
你是一个专业的施工现场安全管理助手，专门负责回答建筑施工安全相关问题，协助进行安全隐患识别和评估。

【功能要求说明】
1. 你可以使用以下工具来帮助用户：
   - analyze_image_tool：分析施工现场图片，识别安全隐患。输入应为图片文件路径。
   - retrieve_knowledge_tool：从知识库中检索相关的建筑施工安全知识。输入为查询关键词。
   - generate_report_tool：生成安全评估报告。输入应为JSON格式的分析结果，或使用默认示例数据。
   - export_pdf_tool：导出PDF报告。输入为报告标题，将生成示例PDF报告。

【任务边界定义】
- 你的工作范围仅限建筑施工安全领域
- 不提供医疗、法律、金融等其他专业领域的建议
- 不处理与建筑施工安全无关的问题

【使用限制条件】
1. 对于 analyze_image_tool：
   - 仅支持 JPG、JPEG、PNG 格式的图片
   - 图片大小不应超过 10MB
   - 输入必须是有效的文件路径
2. 对于 retrieve_knowledge_tool：
   - 仅支持中文查询
   - 查询关键词应与建筑施工安全相关
3. 对于 generate_report_tool：
   - 输入必须是有效的 JSON 格式，包含 "hazards" 字段
   - 如果不提供输入，将使用默认示例数据
4. 对于 export_pdf_tool：
   - 报告标题长度不超过 100 个字符

【工具调用决策逻辑】
- 当用户询问施工安全相关知识时，优先使用 retrieve_knowledge_tool
- 当用户提供图片或要求分析图片时，使用 analyze_image_tool
- 当用户要求生成报告时，使用 generate_report_tool
- 当用户要求导出 PDF 时，使用 export_pdf_tool
- 可以根据需要组合使用多个工具，例如：先分析图片，再检索知识，最后生成报告

【错误处理指引】
- 如果无法理解用户的问题，请明确询问用户需要什么帮助
- 如果工具调用失败，应向用户说明失败原因，并提供替代建议
- 如果超出你的能力范围，应诚实地告知用户
- 所有错误响应应包含错误码（如 [1001]）和清晰的错误描述

【响应要求】
- 回答应专业、准确、简洁
- 使用中文进行交流
- 对于安全隐患，应明确指出风险等级和整改建议
- 输出格式要求：
  - 使用自然语言分段，避免使用 `###` 等markdown标题符号
  - 使用数字编号列出要点，保持层次结构清晰
  - 避免显示任何markdown格式符号
  - 保持行间距适中，内容对齐整齐
  - 开头有简短引言，结尾有总结或后续建议
- 若无法回答则回复：抱歉，无法回答这个问题，请重新提问。
"""

memory = InMemorySaver()
# 创建自定义脱敏中间件


# 自定义中间件，中间件实现脱敏的，去除电话号码和邮箱信息
class DesensitizeDataMiddleware(AgentMiddleware):
    """脱敏中间件"""

    def __init__(self, patterns: list = None):
        super().__init__()
        self.patterns = patterns or [
            (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL]"),
            (r"(\+86)?1[3-9]\d{9}", "[PHONE]"),
        ]

    def _desensitize_text(self, text: str) -> str:
        # 如果内容为空或已经包含脱敏标记，则跳过处理
        if not text or "[EMAIL]" in text or "[PHONE]" in text:
            return text
        # 快速预检查：只有当可能包含敏感信息时才继续处理
        if "@" not in text and not re.search(r"1[3-9]\d{9}", text):
            return text
        logger.debug(f"脱敏前: {text}")
        original_text = text
        for pattern, replacement in self.patterns:
            text = re.sub(pattern, replacement, text)
        # 只有当内容发生变化时才记录日志
        if original_text != text:
            logger.debug(f"脱敏后: {text}")
        return text

    def before_model(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """在模型调用前处理"""
        logger.debug("中间件DesensitizeDataMiddleware - before_model 被调用")
        if "messages" in state:
            messages = state["messages"]
            processed_any = False
            for message in messages:
                if hasattr(message, "content") and isinstance(message.content, str):
                    # 只处理非空内容且未被脱敏的内容
                    if (
                        message.content
                        and "[EMAIL]" not in message.content
                        and "[PHONE]" not in message.content
                    ):
                        # 快速预检查：只有当可能包含敏感信息时才继续处理
                        if "@" in message.content or re.search(
                            r"1[3-9]\d{9}", message.content
                        ):
                            # 只有在真正需要处理时才记录日志
                            if not processed_any:
                                logger.debug("进行脱敏处理.....")
                            original_content = message.content
                            message.content = self._desensitize_text(message.content)
                            # 只有当内容发生变化时才记录
                            if original_content != message.content:
                                logger.debug(f"消息内容已脱敏")
                                processed_any = True
            if processed_any:
                logger.debug("脱敏处理完成！")
        return state

    def after_model(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """在模型调用后处理"""
        # 这里可以添加后处理逻辑
        return state


# 初始化中间件
middle_summary = SummarizationMiddleware(
    model=model,
    trigger=("tokens", 1000),
    keep=("messages", 2),
    summary_prompt="请将以下对话历史进行简洁的摘要，保留关键信息: {messages}",
)
middle_desed = DesensitizeDataMiddleware()

# 定义工具列表
tools = [
    Tool(
        name="analyze_image_tool",
        func=analyze_image_tool,
        description="分析施工现场图片，识别安全隐患。输入应为图片文件路径。【限制：仅支持 JPG/JPEG/PNG 格式，不超过 10MB】",
    ),
    Tool(
        name="retrieve_knowledge_tool",
        func=retrieve_knowledge_tool,
        description="从知识库中检索相关的建筑施工安全知识。输入为查询关键词。【限制：仅限中文查询，与施工安全相关】",
    ),
    Tool(
        name="generate_report_tool",
        func=generate_report_tool,
        description="生成安全评估报告。输入应为JSON格式的分析结果，或使用默认示例数据。【限制：JSON 必须包含 hazards 字段】",
    ),
    Tool(
        name="export_pdf_tool",
        func=export_pdf_tool,
        description="导出PDF报告。输入为报告标题，将生成示例PDF报告。【限制：标题不超过 100 字符】",
    ),
]

agent = create_agent(
    model=model,
    system_prompt=system_prompt,
    tools=tools,
    checkpointer=memory,
    middleware=[middle_summary, middle_desed],
    # debug=True,
)

config = {"configurable": {"thread_id": "用户1"}}


def stream_agent_response(inputs, max_retries=3, retry_delay=1):
    """
    流式生成 Agent 响应（优化版）
    
    Args:
        inputs: 输入消息字典
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        
    Yields:
        响应文本片段
    """
    logger.debug("开始流式响应")
    
    retry_count = 0
    while retry_count <= max_retries:
        try:
            # 获取完整响应
            result = agent.invoke(input=inputs, config=config)
            full_response = result["messages"][-1].content
            
            # 优化后的分段策略：按语义单元分割
            chunks = _split_into_semantic_chunks(full_response)
            
            # 自适应速率控制
            total_chars = len(full_response)
            base_delay = _calculate_optimal_delay(total_chars)
            
            for chunk in chunks:
                yield chunk
                time.sleep(base_delay)
            
            return
            
        except Exception as e:
            retry_count += 1
            logger.warning(f"流式响应尝试 {retry_count}/{max_retries} 失败: {e}")
            
            if retry_count > max_retries:
                logger.error(f"已达最大重试次数，流式响应失败: {e}")
                raise
            
            time.sleep(retry_delay)


def _split_into_semantic_chunks(text):
    """
    将文本按语义单元分割成合适的 chunk
    
    Args:
        text: 完整文本
        
    Returns:
        chunk 列表
    """
    if not text:
        return []
    
    chunks = []
    # 优先按标点符号和换行分割，但保证 chunk 大小合理
    pattern = r'([。！？!?\n]+)'
    parts = re.split(pattern, text)
    
    current_chunk = ""
    min_chunk_size = 2
    max_chunk_size = 8
    
    for i in range(0, len(parts), 2):
        part = parts[i]
        separator = parts[i+1] if i+1 < len(parts) else ""
        
        combined = part + separator
        
        if not combined:
            continue
            
        # 如果当前 chunk + 新内容超过最大，先 yield 当前 chunk
        if len(current_chunk) + len(combined) > max_chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = combined
        else:
            current_chunk += combined
            
        # 如果当前 chunk 足够大，yield 它
        if len(current_chunk) >= min_chunk_size:
            chunks.append(current_chunk)
            current_chunk = ""
    
    # 处理剩余内容
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def _calculate_optimal_delay(total_chars):
    """
    根据文本总长度计算最优延迟时间
    
    Args:
        total_chars: 总字符数
        
    Returns:
        延迟时间（秒）
    """
    if total_chars < 50:
        return 0.08  # 短文本稍慢，更自然
    elif total_chars < 200:
        return 0.05  # 中等文本适中
    else:
        return 0.03  # 长文本稍快，避免等待太久


if __name__ == "__main__":
    print("输入exit退出对话")

    while True:
        user_input = input("用户：")

        if user_input == "exit":
            break

        inputs = {"messages": [{"role": "user", "content": user_input}]}
        
        print("助手：", end="", flush=True)
        full_response = ""
        for chunk in stream_agent_response(inputs):
            print(chunk, end="", flush=True)
            full_response += chunk
        print()  # 换行
