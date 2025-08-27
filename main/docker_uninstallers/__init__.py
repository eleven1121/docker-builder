#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker卸载器工厂模块
根据操作系统类型返回对应的Docker卸载器实例
"""

import platform
import sys
from shared import info

def get_docker_uninstaller():
    """
    工厂函数：根据当前操作系统返回对应的Docker卸载器实例
    
    Returns:
        BaseDockerUninstaller: 对应当前操作系统的Docker卸载器实例
    """
    system = platform.system().lower()
    
    if system == 'linux':
        from .linux_uninstaller import LinuxDockerUninstaller
        info("检测到Linux系统，使用Linux Docker卸载器")
        return LinuxDockerUninstaller()
    
    elif system == 'darwin':
        from .mac_uninstaller import MacDockerUninstaller
        info("检测到macOS系统，使用Mac Docker卸载器")
        return MacDockerUninstaller()
    
    else:
        from .base_uninstaller import DockerUninstallError
        raise DockerUninstallError(f"不支持的操作系统: {system}，目前仅支持Linux和macOS")
