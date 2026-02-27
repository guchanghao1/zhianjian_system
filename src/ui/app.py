"""
建筑施工智能安全助手 - Streamlit 主应用（完全优化版）
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from dotenv import load_dotenv

from src.core.config import DEFAULT_CONFIG, RISK_LEVELS
from src.core.utils import FileUtils, RoutingUtils, TextUtils
from src.core.logging import getLogger
from src.tools import (
    MultimodalAnalyzer,
    KnowledgeRetriever,
    ReportGenerator,
    PDFExporter,
)
from src.ui.html_config import (
    inject_custom_css,
    format_message_html,
    get_welcome_message,
    get_system_settings_message,
    get_loading_message,
    get_error_message,
    get_image_upload_message
)

logger = getLogger(__name__)

load_dotenv()


def create_message(role, content):
    """创建带时间戳和唯一ID的消息对象"""
    return {
        "id": str(uuid.uuid4()),
        "role": role,
        "content": content,
        "timestamp": datetime.now(),
        "is_complete": True
    }


def render_message(message, is_streaming=False):
    """渲染单条消息（自定义气泡样式）"""
    role = message["role"]
    content = message["content"]
    timestamp = message.get("timestamp", datetime.now())

    html = format_message_html(role, content, timestamp, is_streaming)
    st.markdown(html, unsafe_allow_html=True)


@st.cache_resource
def init_tools():
    """初始化工具组件"""
    try:
        multimodal_analyzer = MultimodalAnalyzer()
        knowledge_retriever = KnowledgeRetriever()
        report_generator = ReportGenerator()
        pdf_exporter = PDFExporter()
        return multimodal_analyzer, knowledge_retriever, report_generator, pdf_exporter
    except Exception as e:
        logger.error(f"初始化工具失败: {e}")
        return None, None, None, None


def init_chat():
    """初始化聊天状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "current_streaming_message" not in st.session_state:
        st.session_state.current_streaming_message = None


def init_session_state():
    """初始化会话状态"""
    if "current_report" not in st.session_state:
        st.session_state.current_report = None
    if "current_report_formatted" not in st.session_state:
        st.session_state.current_report_formatted = None
    if "uploaded_image" not in st.session_state:
        st.session_state.uploaded_image = None
    if "image_uploaded" not in st.session_state:
        st.session_state.image_uploaded = False
    if "uploaded_image_path" not in st.session_state:
        st.session_state.uploaded_image_path = None
    if "current_temp_path" not in st.session_state:
        st.session_state.current_temp_path = None
    if "temp_files" not in st.session_state:
        st.session_state.temp_files = []  # 用于跟踪临时文件


def sync_session_state():
    """同步会话状态，确保所有必需状态都已初始化"""
    required_states = {
        "messages": [],
        "is_processing": False,
        "current_streaming_message": None,
        "current_report": None,
        "current_report_formatted": None,
        "uploaded_image": None,
        "image_uploaded": False,
        "uploaded_image_path": None,
        "current_temp_path": None,
        "uploaded_file": None
    }

    for key, default_value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def handle_text_input(prompt, input_mode, chat_history):
    """处理文字输入"""
    if input_mode == "文字输入" and prompt and not st.session_state.get("is_processing", False):
        # 创建并保存用户消息
        user_msg = create_message("user", prompt)
        st.session_state.messages.append(user_msg)
        st.session_state.image_uploaded = False

        # 直接显示用户消息
        with chat_history:
            render_message(user_msg)

        return True
    return False


def handle_image_upload(uploaded_file, chat_history):
    """处理图片上传"""
    if uploaded_file is not None and not st.session_state.get("is_processing", False):
        with st.spinner("正在上传图片..."):
            temp_path = Path(DEFAULT_CONFIG["upload_dir"]) / uploaded_file.name
            FileUtils.ensure_dir(DEFAULT_CONFIG["upload_dir"])

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.session_state.uploaded_image_path = str(temp_path)
            st.session_state.image_uploaded = True
            st.session_state.current_temp_path = str(temp_path)
            st.session_state.uploaded_file = uploaded_file
            
            # 添加到临时文件跟踪列表
            if "temp_files" not in st.session_state:
                st.session_state.temp_files = []
            st.session_state.temp_files.append(str(temp_path))

            is_valid, message = FileUtils.validate_image(str(temp_path))

            if not is_valid:
                st.error(f"❌ {message}")
                # 验证失败时立即清理文件
                try:
                    temp_path.unlink(missing_ok=True)
                    if str(temp_path) in st.session_state.temp_files:
                        st.session_state.temp_files.remove(str(temp_path))
                except:
                    pass
                return False
            else:
                st.success("✅ 图片上传成功")
                logger.info(f"图片上传成功: {temp_path}")
                return True
    return False


def handle_ai_response(chat_history, multimodal_analyzer, knowledge_retriever,
                       report_generator, pdf_exporter, use_cache, report_title, company_name):
    """处理AI响应"""
    if (st.session_state.get("messages") and
            st.session_state.messages and
            st.session_state.messages[-1]["role"] == "user" and
            not st.session_state.get("is_processing", False)):

        last_user_message = st.session_state.messages[-1]["content"]

        try:
            from src.core.agent import stream_agent_response

            st.session_state.is_processing = True

            with chat_history:
                # 初始加载状态
                loading_placeholder = st.empty()
                loading_placeholder.markdown(get_loading_message(), unsafe_allow_html=True)

                full_response = ""
                inputs = {
                    "messages": [{"role": "user", "content": last_user_message}]
                }
                cleaned_inputs = TextUtils.clean_nan_values(inputs)

                # 流式输出
                message_placeholder = st.empty()

                for i, chunk in enumerate(stream_agent_response(cleaned_inputs)):
                    full_response += chunk
                    # 使用柔和的光标闪烁效果
                    cursor = "▌" if i % 3 != 0 else " "

                    # 渲染当前正在生成的消息
                    message_placeholder.markdown(f"""
                    <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 16px;">
                        <div class="message-bubble ai-message">
                            <div style="margin-bottom: 4px;">{full_response}{cursor}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # 清除加载状态
                loading_placeholder.empty()

                # 最终渲染完成的消息并保存到历史
                ai_msg = create_message("assistant", full_response)
                st.session_state.messages.append(ai_msg)
                st.session_state.is_processing = False

                # 清理占位符
                message_placeholder.empty()
                loading_placeholder.empty()
                
                # 重新渲染以显示完整消息
                st.rerun()

        except Exception as e:
            error_msg = f"抱歉，处理您的请求时出错：{str(e)}"
            with chat_history:
                error_placeholder = st.empty()
                error_placeholder.markdown(get_error_message(error_msg), unsafe_allow_html=True)

            # 保存错误消息
            error_msg_obj = create_message("assistant", error_msg)
            st.session_state.messages.append(error_msg_obj)
            st.session_state.is_processing = False
            st.rerun()


def handle_security_assessment(multimodal_analyzer, knowledge_retriever, report_generator,
                               pdf_exporter, use_cache, report_title, company_name):
    """处理安全评估"""
    if st.button("🚀 开始安全评估", type="primary", use_container_width=True):
        with st.spinner("正在进行安全评估，请稍候..."):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.text("步骤 1/5: 分析图片中的安全隐患...")
                progress_bar.progress(20)

                analysis_result = multimodal_analyzer.analyze_image(
                    st.session_state.current_temp_path,
                    use_cache=use_cache,
                )

                if not analysis_result.get("success"):
                    st.error(f"❌ 图片分析失败: {analysis_result.get('error')}")
                    return

                progress_bar.progress(40)
                status_text.text("步骤 2/5: 检索相关安全规范...")

                query = RoutingUtils.extract_hazard_info(analysis_result)
                retrieved_docs = knowledge_retriever.retrieve(
                    query if query else "施工安全", "safe"
                )

                progress_bar.progress(60)
                status_text.text("步骤 3/5: 生成安全评估报告...")

                report_metadata = {
                    "title": report_title,
                    "company": company_name,
                    "date": datetime.now().strftime("%Y年%m月%d日"),
                }

                report_data = report_generator.generate_report(
                    analysis_result,
                    retrieved_docs,
                    report_metadata,
                )

                progress_bar.progress(80)
                status_text.text("步骤 4/5: 准备导出...")

                progress_bar.progress(100)
                status_text.text("✅ 评估完成！")

                st.markdown("---")

                # 评估结果区域
                with st.container():
                    st.subheader("📊 评估结果")

                    hazards = analysis_result.get("hazards", [])
                    if hazards:
                        for i, hazard in enumerate(hazards, 1):
                            severity = hazard.get("severity", "low")
                            risk_info = RISK_LEVELS.get(severity, RISK_LEVELS["low"])

                            with st.expander(f"⚠️ 隐患 {i}: {hazard.get('hazard_type', '未知')}"):
                                st.markdown(f"**严重程度**: :{risk_info['color']}[{risk_info['label']}]")
                                st.markdown(f"**位置**: {hazard.get('location', '未知')}")
                                st.markdown(f"**描述**: {hazard.get('description', '')}")
                                if "confidence" in hazard:
                                    st.markdown(f"**置信度**: {hazard['confidence']:.2%}")
                    else:
                        st.info("✅ 未检测到明显安全隐患")

                st.markdown("---")

                # 报告区域
                with st.container():
                    st.subheader("📄 安全评估报告")

                    formatted_report = report_generator.format_report_for_display(report_data)
                    st.markdown(formatted_report)

                    st.session_state.current_report = report_data
                    st.session_state.current_report_formatted = formatted_report

                st.markdown("---")

                # 导出区域
                with st.container():
                    st.subheader("📥 导出报告")

                    export_col1, export_col2 = st.columns([1, 1])

                    with export_col1:
                        st.download_button(
                            "📄 下载为 Markdown",
                            data=formatted_report,
                            file_name=f"{report_data['report_id']}.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )

                    with export_col2:
                        if st.button("📑 生成并下载 PDF", use_container_width=True):
                            with st.spinner("正在生成 PDF..."):
                                pdf_result = pdf_exporter.export_to_pdf(report_data)

                                if pdf_result.get("success"):
                                    with open(pdf_result["output_path"], "rb") as f:
                                        st.download_button(
                                            "📥 下载 PDF",
                                            data=f,
                                            file_name=pdf_result["filename"],
                                            mime="application/pdf",
                                            use_container_width=True,
                                        )
                                    st.success(f"✅ PDF已生成: {pdf_result['filename']}")
                                else:
                                    st.error(f"❌ PDF生成失败: {pdf_result.get('error')}")

            except Exception as e:
                logger.error(f"安全评估过程出错: {e}")
                st.error(f"❌ 评估过程出错: {str(e)}")


def cleanup_resources():
    """清理资源，防止内存泄漏"""
    # 限制消息历史长度
    if hasattr(st.session_state, 'messages') and len(st.session_state.messages) > 100:
        st.session_state.messages = st.session_state.messages[-50:]
        logger.debug("消息历史已截断")

    # 清理临时文件（排除正在使用的图片）
    temp_files_to_clean = []
    if hasattr(st.session_state, 'temp_files'):
        temp_files_to_clean.extend(st.session_state.temp_files)
    
    # 只有在图片未被使用时才清理
    current_image_path = None
    if hasattr(st.session_state, 'uploaded_image_path'):
        current_image_path = st.session_state.uploaded_image_path
    
    # 过滤掉当前正在显示的图片
    filtered_files = []
    for temp_file in temp_files_to_clean:
        if temp_file != current_image_path:
            filtered_files.append(temp_file)
    
    # 执行文件清理
    cleaned_count = 0
    for temp_file in filtered_files:
        try:
            temp_path = Path(temp_file)
            if temp_path.exists() and temp_path.is_file():
                temp_path.unlink(missing_ok=True)
                cleaned_count += 1
                logger.debug(f"已清理临时文件: {temp_file}")
        except Exception as e:
            logger.warning(f"清理临时文件失败 {temp_file}: {e}")
    
    if cleaned_count > 0:
        logger.info(f"共清理 {cleaned_count} 个临时文件")
    
    # 清空临时文件列表
    if hasattr(st.session_state, 'temp_files'):
        st.session_state.temp_files = []


def main():
    # 注入自定义 CSS
    inject_custom_css()

    # 设置页面配置
    st.set_page_config(
        page_title="建筑施工智能安全助手",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 初始化和同步状态
    init_chat()
    init_session_state()
    sync_session_state()

    # 初始化工具
    multimodal_analyzer, knowledge_retriever, report_generator, pdf_exporter = init_tools()

    # 检查工具初始化
    if not all([multimodal_analyzer, knowledge_retriever, report_generator, pdf_exporter]):
        st.error("❌ 系统初始化失败，请检查配置")
        return

    # 侧边栏配置
    with st.sidebar:
        # 应用标题
        st.title("🏗️ 智能安全助手")
        st.markdown("---")

        # 智能安全助手介绍
        st.markdown("### 🤖 关于智能安全助手")
        st.markdown("""
        <div class="card">
            <p style="font-size: 16px; font-weight: 500; margin-bottom: 12px;">建筑施工智能安全助手是一款基于AI技术的安全评估工具，专为建筑施工现场设计。</p>
            <p style="margin-bottom: 12px;">支持的核心功能：</p>
            <ul style="margin-bottom: 16px;">
                <li style="margin-bottom: 6px;">📝 施工安全问题咨询 - 实时解答安全规范和操作疑问</li>
                <li style="margin-bottom: 6px;">📷 施工场景安全评估 - 上传照片自动识别安全隐患</li>
                <li style="margin-bottom: 6px;">📄 安全评估报告生成 - 自动生成专业的安全评估报告</li>
                <li style="margin-bottom: 6px;">📥 报告导出 - 支持Markdown和PDF格式导出</li>
            </ul>
            <p style="font-size: 15px; color: #666666;">通过上传施工场景照片或直接提问，获取专业的安全评估和建议，帮助您有效识别和防范施工安全风险。</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # 报告设置
        with st.expander("📋 报告设置", expanded=True):
            report_title = st.text_input("报告标题", value="施工现场安全评估报告")
            company_name = st.text_input("公司名称", value="")

        st.markdown("---")

        # 系统设置
        with st.expander("⚙️ 系统设置", expanded=False):
            use_cache = st.checkbox("启用缓存", value=True)
            max_response_length = st.slider("响应长度限制", min_value=500, max_value=5000, value=2000, step=100)
            temperature = st.slider("AI 温度参数", min_value=0.0, max_value=1.0, value=0.7, step=0.1)

        st.markdown("---")

        # 知识库管理
        with st.expander("📚 知识库管理", expanded=False):
            uploaded_doc = st.file_uploader(
                "上传知识库文档",
                type=["pdf", "txt", "docx", "doc"],
                help="上传建筑施工安全规范、标准等文档到知识库",
            )

            if uploaded_doc is not None:
                doc_category = st.selectbox("文档分类", ["safe"])
                if st.button("添加到知识库"):
                    temp_path = Path(DEFAULT_CONFIG["upload_dir"]) / uploaded_doc.name
                    FileUtils.ensure_dir(DEFAULT_CONFIG["upload_dir"])

                    with st.spinner("正在上传文件..."):
                        # 保存文件
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_doc.getbuffer())

                        # 验证文件
                        is_valid = FileUtils.validate_file(str(temp_path))
                        if not is_valid:
                            st.error("❌ 文件验证失败，请检查文件类型和大小")
                        else:
                            with st.spinner("正在处理文档..."):
                                result = knowledge_retriever.add_documents(
                                    str(temp_path), doc_category
                                )
                                if result.get("success"):
                                    st.success(f"✅ 成功添加 {result['num_chunks']} 个文档片段")
                                else:
                                    st.error(f"❌ 添加失败: {result.get('error')}")

        # 系统信息
        st.markdown("---")
        st.markdown("### 📊 系统状态")
        safe_stats = knowledge_retriever.get_collection_stats("safe")
        st.metric(
            label="安全规范文档", value=f"{safe_stats.get('document_count', 0)} 个片段"
        )
        st.metric(
            label="系统状态", value="正常运行"
        )

        st.markdown("---")
        st.markdown("### ⚠️ 危险操作")
        if st.button("🗑️ 清空知识库 (谨慎操作)"):
            if st.checkbox("确认清空所有知识库数据"):
                knowledge_retriever.clear_collection("safe")
                st.success("✅ 知识库已清空")
                st.rerun()

    # 主内容区域
    st.title("建筑施工智能安全助手")
    st.markdown("---")

    # 智能助手区域
    st.header("💬 智能助手")
    st.markdown("通过聊天或上传图片获取安全评估和建议")

    # 聊天框区域
    st.markdown("### 💬 聊天框")
    chat_history = st.container(border=True, height=600, key="chat_container")

    # 输入区域
    st.markdown("### 📝 输入")
    input_container = st.container(border=True)

    # 处理聊天框内容
    with chat_history:
        # 显示已完成的历史消息
        for message in st.session_state.messages:
            if message.get("is_complete", True):
                render_message(message)

        # 处理上传的图片显示
        if st.session_state.image_uploaded:
            st.markdown(get_image_upload_message(), unsafe_allow_html=True)
            st.image(
                st.session_state.uploaded_image_path,
                caption="上传的施工场景照片",
                use_column_width=True  # 使用列宽自适应，避免图片过大
            )

    # 输入模式切换和输入控件
    with input_container:
        # 输入模式切换
        st.markdown("#### 选择输入方式")
        input_mode = st.radio(
            "请选择您的输入方式",
            options=["文字输入", "图片上传"],
            horizontal=True,
            key="input_mode",
            help="文字输入用于咨询问题，图片上传用于场景安全评估"
        )

        prompt = None
        uploaded_file = None

        if input_mode == "文字输入":
            # 文字输入框
            prompt = st.chat_input(
                placeholder="输入您的问题或指令...",
                key="chat_input"
            )
            # 保持已上传的图片（如果存在）
            if st.session_state.image_uploaded:
                uploaded_file = st.session_state.get("uploaded_file", None)
        else:
            # 图片上传
            uploaded_file = st.file_uploader(
                "上传施工场景照片",
                type=["jpg", "jpeg", "png"],
                help="上传施工场景照片进行安全评估",
                key="file_uploader"
            )
            # 清除文字输入
            prompt = None

    # 处理用户交互
    text_processed = handle_text_input(prompt, input_mode, chat_history)

    if not text_processed:  # 只有文字输入未处理时才处理图片
        image_processed = handle_image_upload(uploaded_file, chat_history)

        if image_processed:
            st.markdown("---")

            # 评估按钮区域
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                handle_security_assessment(
                    multimodal_analyzer, knowledge_retriever, report_generator,
                    pdf_exporter, use_cache, report_title, company_name
                )

            with col_btn2:
                if st.button("❌ 取消", use_container_width=True):
                    # 清理上传的图片文件
                    if hasattr(st.session_state, 'uploaded_image_path') and st.session_state.uploaded_image_path:
                        try:
                            temp_path = Path(st.session_state.uploaded_image_path)
                            if temp_path.exists():
                                temp_path.unlink(missing_ok=True)
                                logger.info(f"已删除取消的图片文件: {st.session_state.uploaded_image_path}")
                        except Exception as e:
                            logger.warning(f"删除图片文件失败: {e}")
                    
                    # 重置状态
                    st.session_state.image_uploaded = False
                    st.session_state.uploaded_image_path = None
                    st.session_state.uploaded_file = None
                    st.session_state.current_temp_path = None
                    st.rerun()

    # 处理AI响应（放在最后，确保状态已更新）
    handle_ai_response(
        chat_history, multimodal_analyzer, knowledge_retriever,
        report_generator, pdf_exporter, use_cache, report_title, company_name
    )

    # 清理资源
    cleanup_resources()


if __name__ == "__main__":
    main()
