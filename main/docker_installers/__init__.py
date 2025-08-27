#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker安装器工厂模块
根据操作系统类型返回对应的Docker安装器实例
"""

import platform
import sys
from shared import info

def get_docker_installer():
    """
    工厂函数：根据当前操作系统返回对应的Docker安装器实例
    
    Returns:
        BaseDockerInstaller: 对应当前操作系统的Docker安装器实例
    """
    system = platform.system().lower()
    
    if system == 'linux':
        from .linux_installer import LinuxDockerInstaller
        info("检测到Linux系统，使用Linux Docker安装器")
        return LinuxDockerInstaller()
    
    elif system == 'darwin':
        from .mac_installer import MacDockerInstaller
        info("检测到macOS系统，使用Mac Docker安装器")
        return MacDockerInstaller()
    
    else:
        from .base_installer import DockerInstallError
        raise DockerInstallError(f"不支持的操作系统: {system}，目前仅支持Linux和macOS")
