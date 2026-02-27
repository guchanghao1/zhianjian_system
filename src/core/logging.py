#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一日志系统模块
为整个应用提供统一的日志配置和接口
"""

import sys
from datetime import datetime


class SimpleLogger:
    """改进的日志类，支持更多功能"""

    # 日志级别
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    # 日志级别优先级
    _LEVEL_PRIORITY = {
        DEBUG: 0,
        INFO: 1,
        WARNING: 2,
        ERROR: 3,
        CRITICAL: 4
    }
    
    # 颜色映射（用于终端输出）
    _COLOR_MAP = {
        DEBUG: "\033[36m",      # 青色
        INFO: "\033[32m",       # 绿色
        WARNING: "\033[33m",    # 黄色
        ERROR: "\033[31m",      # 红色
        CRITICAL: "\033[35m",   # 紫色
    }
    _RESET_COLOR = "\033[0m"

    def __init__(self, name, log_file="loggings.txt", level="INFO", enable_colors=True):
        self.name = name
        self.log_file = log_file
        self.level = level
        # 文件日志不使用颜色，终端输出可选使用颜色
        self.enable_colors = enable_colors and self._supports_color()
        self._file_colors_enabled = False  # 文件日志禁用颜色
        self._ensure_log_dir()
        
    def _supports_color(self):
        """检查终端是否支持颜色输出"""
        try:
            import sys
            return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        except:
            return False

    def _ensure_log_dir(self):
        """确保日志文件目录存在"""
        from pathlib import Path
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def _format_message(self, level, message, for_file=False):
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"{timestamp} {level} [{self.name}] {message}"
        
        # 终端输出添加颜色（如果启用且支持）
        if not for_file and self.enable_colors and level in self._COLOR_MAP:
            color = self._COLOR_MAP[level]
            formatted_msg = f"{color}{formatted_msg}{self._RESET_COLOR}"
            
        return formatted_msg

    def _should_log(self, level):
        """判断是否应该记录该级别的日志"""
        return self._LEVEL_PRIORITY.get(level, 0) >= self._LEVEL_PRIORITY.get(self.level, 1)

    def _write_to_file(self, message):
        """写入日志到文件（无颜色代码）"""
        try:
            # 清理ANSI颜色代码
            import re
            clean_message = re.sub(r'\033\[[0-9;]*m', '', message)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(clean_message + "\n")
        except Exception:
            # 避免日志写入失败影响主程序
            pass

    def debug(self, message):
        """输出调试信息"""
        self._log(self.DEBUG, message)

    def info(self, message):
        """输出信息"""
        self._log(self.INFO, message)

    def warning(self, message):
        """输出警告"""
        self._log(self.WARNING, message)

    def error(self, message):
        """输出错误"""
        self._log(self.ERROR, message)

    def critical(self, message):
        """输出严重错误"""
        self._log(self.CRITICAL, message)
        
    def _log(self, level, message):
        """统一的日志记录方法"""
        if self._should_log(level):
            formatted_message = self._format_message(level, message)
            print(formatted_message)
            self._write_to_file(formatted_message)

    def setLevel(self, level):
        """设置日志级别"""
        self.level = level


# 模拟logging模块的getLogger函数
def getLogger(name=None, log_file="loggings.txt", level="INFO", enable_colors=True):
    """获取日志器"""
    return SimpleLogger(name or "__main__", log_file=log_file, level=level, enable_colors=enable_colors)


def get_logger(name=None, log_file="loggings.txt", level="INFO", enable_colors=True):
    """获取日志器（与原始接口兼容）"""
    return getLogger(name, log_file=log_file, level=level, enable_colors=enable_colors)


# 兼容旧接口
def get_logger(name=None, log_file="loggings.txt", level="INFO"):
    """获取日志器（与原始接口兼容）"""
    return getLogger(name, log_file=log_file, level=level)


# 模拟setup_logging函数
def setup_logging(args=None):
    """设置日志配置（模拟函数，保持接口兼容）"""
    return args


# 导出所有必要的组件
__all__ = ["setup_logging", "get_logger", "getLogger", "SimpleLogger"]

# 确保日志系统被正确初始化
# 注意：实际初始化应该在应用启动时进行，这里仅提供接口
