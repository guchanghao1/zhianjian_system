"""
HTML和CSS配置文件
包含应用中所有的HTML和CSS相关配置
"""

import streamlit as st
from datetime import datetime


def inject_custom_css():
    """注入自定义 CSS 样式"""
    st.markdown("""
    <style>
        /* 全局样式 */
        * {
            box-sizing: border-box;
        }
        
        /* 主题色定义 */
        :root {
            --primary-color: #1e88e5;
            --primary-dark: #1565c0;
            --secondary-color: #42a5f5;
            --background-color: #f8f9fa;
            --surface-color: #ffffff;
            --text-primary: #333333;
            --text-secondary: #666666;
            --border-color: #e0e0e0;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --error-color: #f44336;
            --info-color: #2196f3;
        }
        
        /* 页面背景 */
        body {
            background-color: var(--background-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: var(--text-primary);
        }
        
        /* 主容器 */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* 聊天容器样式 */
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding: 20px;
            background-color: var(--surface-color);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        /* 消息气泡基础样式 */
        .message-bubble {
            max-width: 80%;
            padding: 16px 20px;
            border-radius: 20px;
            word-wrap: break-word;
            position: relative;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            line-height: 1.5;
        }
        
        .message-bubble:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        
        /* 用户消息 - 右侧对齐 */
        .user-message {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            color: white;
            border-bottom-right-radius: 6px;
        }
        
        /* AI 消息 - 左侧对齐 */
        .ai-message {
            align-self: flex-start;
            background: var(--surface-color);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-bottom-left-radius: 6px;
        }
        
        /* 消息元数据（发送者+时间） */
        .message-meta {
            font-size: 13px;
            opacity: 0.7;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .user-message .message-meta {
            justify-content: flex-end;
        }
        
        /* 发送者头像/图标 */
        .sender-icon {
            font-size: 16px;
            margin-right: 6px;
        }
        
        /* 聊天框整体样式 */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px;
            overflow: hidden;
        }
        
        /* 滚动到最新消息 */
        .stChatMessage {
            scroll-margin-top: 24px;
        }
        
        /* 按钮样式优化 */
        .stButton > button {
            border-radius: 10px;
            transition: all 0.3s ease;
            font-weight: 500;
            font-size: 15px;
            padding: 10px 20px;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* 主要按钮样式 */
        .stButton > button:first-child {
            background-color: var(--primary-color);
            color: white;
            border: none;
        }
        
        .stButton > button:first-child:hover {
            background-color: var(--primary-dark);
        }
        
        /* 输入框样式 */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 1px solid var(--border-color);
            padding: 12px 16px;
            font-size: 16px;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.1);
        }
        
        /* 聊天输入框样式 */
        .stChatInput > div > div > input {
            border-radius: 20px;
            border: 1px solid var(--border-color);
            padding: 12px 16px;
            font-size: 16px;
        }
        
        /* 标签样式 */
        label {
            font-size: 15px;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 8px;
            display: block;
        }
        
        /* 文件上传样式 */
        .stFileUploader > div > div {
            border-radius: 10px;
            border: 2px dashed var(--border-color);
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .stFileUploader > div > div:hover {
            border-color: var(--primary-color);
            background-color: rgba(30, 136, 229, 0.05);
        }
        
        /* 卡片样式 */
        .stExpander {
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 16px;
            overflow: hidden;
        }
        
        /* 标签页样式 */
        .stTabs > div > div {
            border-radius: 12px;
            overflow: hidden;
        }
        
        /* 侧边栏样式 */
        .stSidebar {
            background-color: var(--surface-color);
            border-right: 1px solid var(--border-color);
        }
        
        /* 侧边栏标题 */
        .stSidebar h1, .stSidebar h2, .stSidebar h3 {
            color: var(--text-primary);
            font-weight: 600;
        }
        
        /* 分隔线 */
        hr {
            border: none;
            height: 1px;
            background-color: var(--border-color);
            margin: 20px 0;
        }
        
        /* 响应式设计 */
        @media screen and (max-width: 768px) {
            .main-container {
                padding: 10px;
            }
            
            .message-bubble {
                max-width: 90%;
                padding: 14px 18px;
            }
            
            .stColumns {
                flex-direction: column;
            }
            
            .stColumn {
                width: 100% !important;
                margin-bottom: 16px;
            }
            
            .stSidebar {
                width: 100% !important;
                border-right: none;
                border-bottom: 1px solid var(--border-color);
            }
            
            .chat-container {
                padding: 16px;
            }
        }
        
        /* 针对平板设备 */
        @media screen and (min-width: 769px) and (max-width: 1024px) {
            .message-bubble {
                max-width: 75%;
            }
        }
        
        /* 浏览器兼容性 */
        /* 针对IE11的兼容性 */
        @media all and (-ms-high-contrast: none), (-ms-high-contrast: active) {
            .message-bubble {
                max-width: 80%;
            }
        }
        
        /* 针对Safari的兼容性 */
        @supports (-webkit-appearance: none) {
            .message-bubble {
                -webkit-border-radius: 20px;
            }
        }
        
        /* 加载动画 */
        @keyframes pulse {
            0% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
            100% {
                opacity: 1;
            }
        }
        
        @keyframes dots {
            0%, 20% {
                content: ".";
            }
            40% {
                content: "..";
            }
            60%, 100% {
                content: "...";
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .loading {
            animation: pulse 1.5s infinite;
        }
        
        .loading-dots span {
            animation: pulse 1.4s infinite ease-in-out both;
        }
        
        .loading-dots span:nth-child(1) {
            animation-delay: -0.32s;
        }
        
        .loading-dots span:nth-child(2) {
            animation-delay: -0.16s;
        }
        
        /* 消息动画 */
        .message-bubble {
            animation: fadeIn 0.3s ease-out;
        }
        
        /* 报告样式 */
        .report-section {
            background: var(--surface-color);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid var(--border-color);
        }
        
        /* 危险等级标签 */
        .risk-level {
            padding: 6px 16px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
            margin-right: 8px;
        }
        
        .risk-high {
            background: #fee2e2;
            color: #dc2626;
        }
        
        .risk-medium {
            background: #fef3c7;
            color: #d97706;
        }
        
        .risk-low {
            background: #d1fae5;
            color: #059669;
        }
        
        /* 进度条样式 */
        .stProgress > div > div {
            border-radius: 6px;
            background-color: var(--primary-color);
        }
        
        /* 标题样式 */
        h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 24px;
            line-height: 1.3;
        }
        
        h2 {
            font-size: 24px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 20px;
            line-height: 1.4;
        }
        
        h3 {
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 18px;
            line-height: 1.4;
        }
        
        h4 {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            line-height: 1.5;
        }
        
        h5, h6 {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 14px;
            line-height: 1.5;
        }
        
        /* 文本样式 */
        p {
            color: var(--text-secondary);
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 16px;
        }
        
        /* 列表样式 */
        ul, ol {
            margin-bottom: 20px;
            padding-left: 28px;
        }
        
        li {
            color: var(--text-secondary);
            font-size: 16px;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        /* 卡片式容器 */
        .card {
            background-color: var(--surface-color);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
        }
        
        /* 表单元素样式 */
        .stTextInput, .stSelectbox, .stCheckbox {
            margin-bottom: 16px;
        }
        
        /* 错误消息样式 */
        .stError {
            background-color: rgba(244, 67, 54, 0.1);
            border-left: 4px solid var(--error-color);
            border-radius: 8px;
            padding: 12px 16px;
        }
        
        /* 图片显示优化 */
        .stImage img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 8px 0;
        }
        
        /* 聊天区域图片限制 */
        [data-testid="stContainer"] .stImage img {
            max-height: 300px;
            object-fit: contain;
            margin: 16px 0;
        }
        
        /* 成功消息样式 */
        .stSuccess {
            background-color: rgba(76, 175, 80, 0.1);
            border-left: 4px solid var(--success-color);
            border-radius: 8px;
            padding: 12px 16px;
            margin: 16px 0;
        }
        
        /* 信息消息样式 */
        .stInfo {
            background-color: rgba(33, 150, 243, 0.1);
            border-left: 4px solid var(--info-color);
            border-radius: 8px;
            padding: 12px 16px;
            margin: 16px 0;
        }
        
        /* 警告消息样式 */
        .stWarning {
            background-color: rgba(255, 152, 0, 0.1);
            border-left: 4px solid var(--warning-color);
            border-radius: 8px;
            padding: 12px 16px;
            margin: 16px 0;
        }
    </style>
    """, unsafe_allow_html=True)


def format_timestamp(dt):
    """格式化时间戳为友好显示格式"""
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    elif (now - dt).days == 1:
        return f"昨天 {dt.strftime('%H:%M')}"
    else:
        return dt.strftime("%m-%d %H:%M")


def format_message_html(role, content, timestamp, is_streaming=False):
    """格式化消息HTML（缓存以提高性能）"""
    formatted_time = format_timestamp(timestamp)
    bubble_class = "user-message" if role == "user" else "ai-message"
    sender_icon = "👤" if role == "user" else "🤖"
    sender_name = "您" if role == "user" else "智能助手"
    
    return f"""
    <div style="display: flex; flex-direction: column; {'align-items: flex-end;' if role == 'user' else 'align-items: flex-start;'} margin-bottom: 16px;">
        <div class="message-bubble {bubble_class}">
            <div style="margin-bottom: 4px;">{content}</div>
            <div class="message-meta">
                <span class="sender-icon">{sender_icon}</span>
                <span>{sender_name}</span>
                <span>·</span>
                <span>{formatted_time}</span>
            </div>
        </div>
    </div>
    """


def get_welcome_message():
    """获取欢迎消息HTML"""
    return """
    <div class="card">
        <h3>🤖 智能安全助手</h3>
        <p>可以直接与智能助手对话，询问施工安全相关问题，或上传图片进行安全评估。</p>
        <p>支持的功能：</p>
        <ul>
            <li>📝 施工安全问题咨询</li>
            <li>📷 施工场景安全评估</li>
            <li>📄 安全评估报告生成</li>
            <li>📥 报告导出（Markdown/PDF）</li>
        </ul>
    </div>
    """


def get_system_settings_message():
    """获取系统设置消息HTML"""
    return """
    <div class="card">
        <h4>🔧 系统配置</h4>
        <p>这里可以查看和管理系统的各项设置。</p>
    </div>
    """


def get_loading_message():
    """获取加载消息HTML"""
    return """
    <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 16px;">
        <div class="message-bubble ai-message loading">
            <div style="margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                <span>🤔 正在思考...</span>
                <span class="loading-dots">
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                </span>
            </div>
        </div>
    </div>
    """


def get_error_message(error_msg):
    """获取错误消息HTML"""
    return f"""
    <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 16px;">
        <div class="message-bubble ai-message">
            <div style="margin-bottom: 4px; color: #dc2626;">{error_msg}</div>
        </div>
    </div>
    """


def get_image_upload_message():
    """获取图片上传消息HTML"""
    return """
    <div style="display: flex; flex-direction: column; align-items: flex-end; margin-bottom: 16px;">
        <div class="message-bubble user-message">
            <div style="margin-bottom: 8px;">上传了施工场景照片</div>
        </div>
    </div>
    """
