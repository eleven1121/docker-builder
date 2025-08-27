#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker检查工厂模块
根据操作系统类型返回合适的Docker检查器实例
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error
from main.check_system import is_linux, is_mac, is_windows
from .base_checker import DockerChecker
from .linux_checker import LinuxDockerChecker
from .mac_checker import MacDockerChecker


def get_docker_checker() -> DockerChecker:
    """
    工厂函数：根据当前操作系统返回合适的Docker检查器
    
    Returns:
        DockerChecker: Docker检查器实例
        
    Raises:
        RuntimeError: 如果当前操作系统不支持
    """
    if is_linux():
        info("检测到Linux系统，使用Linux Docker检查器")
        return LinuxDockerChecker()
    elif is_mac():
        info("检测到macOS系统，使用Mac Docker检查器")
        return MacDockerChecker()
    elif is_windows():
        warning("Windows支持尚未实现")
        raise RuntimeError("Windows系统尚不支持Docker检查")
    else:
        error("未知操作系统")
        raise RuntimeError("不支持的操作系统")
