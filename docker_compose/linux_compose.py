#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux系统Docker Compose安装模块
提供在Linux系统上安装和重新安装Docker Compose的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from shared.run_command import run_command, CommandError
from docker_compose.compose_manager import ComposeError, get_compose_version


def install_compose_on_linux(version=None):
    """
    在Linux上安装Docker Compose
    
    Args:
        version: 指定要安装的版本，如果为None则安装最新版本
        
    Returns:
        bool: 安装成功返回True
        
    Raises:
        ComposeError: 安装失败时抛出异常
    """
    info("在Linux上安装Docker Compose...")
    
    # 尝试使用包管理器安装
    try:
        # 检查是哪种Linux发行版
        if os.path.exists("/usr/bin/apt-get"):  # Debian/Ubuntu
            run_command("sudo apt-get update", verbose=True)
            run_command("sudo apt-get install -y docker-compose", verbose=True)
        elif os.path.exists("/usr/bin/yum"):  # CentOS/RHEL
            run_command("sudo yum install -y docker-compose", verbose=True)
        else:
            # 如果包管理器安装不可用，使用pip安装
            run_command("sudo pip3 install docker-compose", verbose=True)
        
        success("Docker Compose已成功安装")
        return True
    except Exception as e:
        warning(f"使用包管理器安装失败: {str(e)}，尝试使用pip安装...")
        
        # 尝试使用pip安装
        try:
            run_command("sudo pip3 install docker-compose", verbose=True)
            success("Docker Compose已通过pip成功安装")
            return True
        except Exception as pip_error:
            error(f"使用pip安装Docker Compose失败: {str(pip_error)}")
            raise ComposeError(f"在Linux上安装Docker Compose失败: {str(pip_error)}")


def reinstall_compose_on_linux(version=None):
    """
    在Linux上重新安装Docker Compose
    
    Args:
        version: 指定要安装的版本，如果为None则安装最新版本
        
    Returns:
        bool: 安装成功返回True
        
    Raises:
        ComposeError: 安装失败时抛出异常
    """
    info("在Linux上重新安装Docker Compose...")
    
    # 首先尝试卸载现有的Docker Compose
    try:
        if os.path.exists("/usr/local/bin/docker-compose"):
            run_command("sudo rm /usr/local/bin/docker-compose", check=False, verbose=True)
        
        # 尝试使用pip卸载
        run_command("sudo pip3 uninstall -y docker-compose", check=False, verbose=True)
        
        # 尝试使用包管理器卸载
        if os.path.exists("/usr/bin/apt-get"):
            run_command("sudo apt-get remove -y docker-compose", check=False, verbose=True)
        elif os.path.exists("/usr/bin/yum"):
            run_command("sudo yum remove -y docker-compose", check=False, verbose=True)
    except Exception as e:
        warning(f"卸载Docker Compose时出现警告（这可能不是问题）: {str(e)}")
    
    # 安装新版本
    info("开始安装Docker Compose...")
    return install_compose_on_linux(version=version)
