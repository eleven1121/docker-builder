#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
macOS系统Docker Compose安装模块
提供在macOS系统上安装和重新安装Docker Compose的功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from shared.run_command import run_command, CommandError
from docker_compose.compose_manager import ComposeError, get_compose_version


def install_compose_on_mac(version=None):
    """
    在Mac上安装Docker Compose
    
    Args:
        version: 指定要安装的版本，如果为None则安装最新版本
        
    Returns:
        bool: 安装成功返回True
        
    Raises:
        ComposeError: 安装失败时抛出异常
    """
    info("在Mac上安装Docker Compose...")
    
    # 在Mac上，Docker Compose通常与Docker Desktop一起安装
    # 首先检查Docker Desktop是否已安装
    if not os.path.exists("/Applications/Docker.app"):
        warning("未检测到Docker Desktop，Docker Compose通常随Docker Desktop一起安装")
        warning("请先安装Docker Desktop: https://docs.docker.com/desktop/install/mac-install/")
        
        # 如果用户仍希望单独安装Docker Compose，可以使用brew或pip
        if input("是否仍希望尝试使用Homebrew安装Docker Compose? (y/n): ").lower() == 'y':
            try:
                run_command("brew install docker-compose", verbose=True)
                success("Docker Compose已通过Homebrew成功安装")
                return True
            except Exception as e:
                warning(f"使用Homebrew安装失败: {str(e)}，尝试使用pip安装...")
                
                try:
                    run_command("pip3 install docker-compose", verbose=True)
                    success("Docker Compose已通过pip成功安装")
                    return True
                except Exception as pip_error:
                    error(f"使用pip安装Docker Compose失败: {str(pip_error)}")
                    raise ComposeError(f"在Mac上安装Docker Compose失败: {str(pip_error)}")
        else:
            raise ComposeError("取消安装Docker Compose")
    else:
        info("检测到Docker Desktop已安装，Docker Compose应该已经可用")
        
        # 验证Docker Compose是否可用
        compose_version = get_compose_version()
        if compose_version:
            success(f"Docker Compose已可用（版本: {compose_version}）")
            return True
        else:
            warning("Docker Desktop已安装，但Docker Compose不可用，尝试使用pip安装")
            try:
                run_command("pip3 install docker-compose", verbose=True)
                success("Docker Compose已通过pip成功安装")
                return True
            except Exception as e:
                error(f"使用pip安装Docker Compose失败: {str(e)}")
                raise ComposeError(f"在Mac上安装Docker Compose失败: {str(e)}")


def reinstall_compose_on_mac(version=None):
    """
    在Mac上重新安装Docker Compose
    
    Args:
        version: 指定要安装的版本，如果为None则安装最新版本
        
    Returns:
        bool: 安装成功返回True
        
    Raises:
        ComposeError: 安装失败时抛出异常
    """
    info("在Mac上重新安装Docker Compose...")
    
    # 首先尝试卸载现有的Docker Compose
    try:
        # 在Mac上，通过pip卸载
        run_command("pip3 uninstall -y docker-compose", check=False, verbose=True)
        # 如果通过brew安装，也尝试卸载
        run_command("brew uninstall docker-compose", check=False, verbose=True)
    except Exception as e:
        warning(f"卸载Docker Compose时出现警告（这可能不是问题）: {str(e)}")
    
    # 安装新版本
    info("开始安装Docker Compose...")
    return install_compose_on_mac(version=version)
