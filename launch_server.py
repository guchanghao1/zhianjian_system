#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义服务器启动脚本 - 优化版本

功能:
- 启动Streamlit服务器
- 自动打开浏览器访问前端
- 提供详细的日志输出
- 检查应用文件是否存在
- 支持传递额外的命令行参数

使用方法:
  python launch_server.py

访问地址:
  http://127.0.0.1:8000
"""

import subprocess
import sys
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    format='%(asctime)s %(levelname)s [launch_server] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def launch_streamlit():
    """启动Streamlit服务器到指定地址和端口"""
    project_root = Path(__file__).parent
    app_path = project_root / "src" / "ui" / "app.py"
    
    # 打印当前路径信息，方便调试
    logger.debug(f"当前文件路径: {Path(__file__)}")
    logger.debug(f"项目根目录: {project_root}")
    logger.debug(f"应用文件路径: {app_path}")

    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="启动建筑施工智能安全助手服务器"
    )
    
    # 解析参数
    args, remaining_args = parser.parse_known_args()
    
    # 检查应用文件是否存在
    if not app_path.exists():
        logger.error(f"应用文件不存在: {app_path}")
        sys.exit(1)

    # 构建命令 - 使用基本的Streamlit参数
    # Streamlit默认会自动打开浏览器，我们不再重复打开
    cmd = [
        "streamlit",
        "run",
        str(app_path),
        "--server.address", "127.0.0.1",
        "--server.port", "8000",
    ]
    
    # 添加剩余参数
    cmd.extend(remaining_args)

    logger.info("启动Streamlit服务器...")
    logger.info(f"访问地址: http://127.0.0.1:8000")
    logger.info("浏览器将自动打开")
    logger.info("按 Ctrl+C 停止服务器")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("服务器已停止")


if __name__ == "__main__":
    launch_streamlit()
