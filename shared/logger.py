#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Color-coded logging utility for command-line applications.
"""

import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class TextColor(Enum):
    """ANSI color codes for terminal text coloring."""
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ColoredFormatter(logging.Formatter):
    """自定义带颜色的日志格式化器。"""
    
    def __init__(self, fmt: str = "[{timestamp}] [{level_name}] {message}"):
        super().__init__()
        self.fmt = fmt
    
    COLORS = {
        logging.DEBUG: TextColor.BRIGHT_BLUE.value,
        logging.INFO: TextColor.BRIGHT_CYAN.value,
        logging.WARNING: TextColor.BRIGHT_YELLOW.value,
        logging.ERROR: TextColor.BRIGHT_RED.value,
        logging.CRITICAL: TextColor.BRIGHT_MAGENTA.value + TextColor.BOLD.value,
        25: TextColor.BRIGHT_GREEN.value + TextColor.BOLD.value,  
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with appropriate colors."""
        color = self.COLORS.get(record.levelno, TextColor.RESET.value)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # SUCCESS 级别使用勾勾图标并移除方括号
        if record.levelno == 25:  # SUCCESS 级别的数值是25
            # 为 SUCCESS 使用特殊格式，完全去除方括号
            return f"{timestamp} {color}✓ {record.getMessage()}{TextColor.RESET.value}"
        else:
            level_name = f"{color}{record.levelname}{TextColor.RESET.value}"
            message = f"{color}{record.getMessage()}{TextColor.RESET.value}"
            
            return self.fmt.format(
                timestamp=timestamp,
                level_name=level_name,
                message=message
            )

# 在模块级别定义单例实例变量
_logger_instance = None

# 在 get_logger 中允许自定义格式
def get_logger(name: str = "docker-builder", level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    创建并返回带有彩色控制台输出的 logger。
    
    Args:
        name (str): logger 的名称
        level (int): 日志级别阈值
    
    Returns:
        logging.Logger: 配置好的 logger 实例
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance
        
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    
    # 如果提供了日志文件路径，则添加文件处理器
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
            logger.addHandler(file_handler)
        except Exception as e:
            # 使用原始 print 避免递归日志问题
            print(f"无法创建日志文件: {str(e)}")
    
    logger.addHandler(console_handler)
    _logger_instance = logger
    return logger


# Singleton logger instance for easy import
logger = get_logger()


# Convenience methods
def debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """Log a debug message."""
    logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log an info message."""
    logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log a warning message."""
    logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log an error message."""
    logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log a critical message."""
    logger.critical(msg, *args, **kwargs)


# 自定义SUCCESS日志级别（位于INFO和WARNING之间）
SUCCESS = 25
logging.addLevelName(SUCCESS, 'SUCCESS')

def success(msg, *args, **kwargs):
    """Log a success message."""
    logger.log(SUCCESS, msg, *args, **kwargs)

def set_level(level):
    """Set the logging level."""
    logger.setLevel(level)


# Example usage
if __name__ == "__main__":
    debug("This is a debug message")
    info("This is an info message")
    warning("This is a warning message")
    error("This is an error message")
    critical("This is a critical message")
