#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker Compose 管理模块
提供Docker Compose的安装、状态检查、重装和服务启动功能
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from shared.run_command import run_command, CommandError

# 导入特定系统的Compose安装模块
from docker_compose.linux_compose import install_compose_on_linux, reinstall_compose_on_linux
from docker_compose.mac_compose import install_compose_on_mac, reinstall_compose_on_mac


class ComposeError(Exception):
    """Docker Compose操作异常"""
    pass


def get_compose_cmd():
    """
    获取docker-compose命令
    
    根据当前环境返回合适的docker-compose命令
    在新版Docker中，命令可能是"docker compose"而不是"docker-compose"
    
    Returns:
        str: docker-compose命令
    """
    try:
        # 首先尝试旧版命令
        result = run_command("docker-compose --version", check=False, verbose=False)
        if result.returncode == 0:
            return "docker-compose"
        
        # 尝试新版命令格式
        result = run_command("docker compose version", check=False, verbose=False)
        if result.returncode == 0:
            return "docker compose"
        
        # 如果都不可用，则返回默认的新版命令格式
        return "docker compose"
    except Exception as e:
        debug(f"获取docker-compose命令时出错: {str(e)}")
        return "docker compose"  # 默认使用新版命令格式


def get_compose_version():
    """
    获取Docker Compose版本
    
    Returns:
        str: Docker Compose版本号，如果未安装则返回None
    """
    try:
        compose_cmd = get_compose_cmd()
        version_cmd = f"{compose_cmd} version"
        if compose_cmd == "docker compose":
            # 新版Docker Compose集成在Docker CLI中
            version_cmd = "docker compose version"
        
        result = run_command(version_cmd, check=False, verbose=False)
        if result.returncode != 0:
            return None
        
        # 解析版本号
        version_output = result.stdout.lower()
        if "version" in version_output:
            # 提取版本号
            import re
            version_match = re.search(r"version\s+v?([0-9.]+)", version_output)
            if version_match:
                return version_match.group(1)
        
        return "未知版本"
    except Exception as e:
        debug(f"获取Docker Compose版本时出错: {str(e)}")
        return None


def install_compose(version=None, force=False):
    """
    安装Docker Compose
    
    Args:
        version: 指定要安装的版本，如果为None则安装最新版本
        force: 是否强制安装，即使已经安装了Docker Compose
        
    Returns:
        bool: 安装成功返回True，已安装且未强制安装返回False
    
    Raises:
        ComposeError: 安装失败时抛出异常
    """
    # 检查是否已安装
    current_version = get_compose_version()
    if current_version and not force:
        info(f"Docker Compose已安装（版本: {current_version}），无需重新安装")
        return False
    
    # 根据操作系统选择安装方法
    os_type = platform.system().lower()
    try:
        if os_type == "linux":
            return install_compose_on_linux(version)
        elif os_type == "darwin":
            return install_compose_on_mac(version)
        else:
            raise ComposeError(f"不支持的操作系统: {os_type}")
    except Exception as e:
        error(f"安装Docker Compose失败: {str(e)}")
        raise ComposeError(f"安装Docker Compose失败: {str(e)}")

def is_compose_running():
    """
    检查Docker Compose是否正常运行
    
    Returns:
        bool: 如果Docker Compose可用且可以正常运行，返回True，否则返回False
    """
    try:
        # 检查Docker Compose是否已安装
        compose_cmd = get_compose_cmd()
        
        # 尝试运行一个简单的Docker Compose命令
        result = run_command(f"{compose_cmd} version", check=False, verbose=False)
        
        return result.returncode == 0
    except Exception as e:
        debug(f"检查Docker Compose状态时出错: {str(e)}")
        return False


def reinstall_compose(version=None):
    """
    重新安装Docker Compose
    
    Args:
        version: 指定要安装的版本，如果为None则安装最新版本
        
    Returns:
        bool: 重新安装成功返回True
    
    Raises:
        ComposeError: 重新安装失败时抛出异常
    """
    info("开始重新安装Docker Compose...")
    
    # 根据操作系统选择重新安装方法
    os_type = platform.system().lower()
    try:
        if os_type == "linux":
            return reinstall_compose_on_linux(version)
        elif os_type == "darwin":
            return reinstall_compose_on_mac(version)
        else:
            raise ComposeError(f"不支持的操作系统: {os_type}")
    except Exception as e:
        error(f"重新安装Docker Compose失败: {str(e)}")
        raise ComposeError(f"重新安装Docker Compose失败: {str(e)}")


def start_service_by_compose(compose_file, project_name=None, services=None, detached=True, build=False):
    """
    使用Docker Compose启动服务
    
    Args:
        compose_file: Docker Compose文件路径
        project_name: 项目名称，如果为None则使用目录名称
        services: 要启动的服务列表，如果为None则启动所有服务
        detached: 是否在后台运行
        build: 是否在启动前构建镜像
        
    Returns:
        bool: 启动成功返回True
    
    Raises:
        ComposeError: 启动失败时抛出异常
    """
    try:
        # 检查Docker Compose是否可用
        if not is_compose_running():
            error("Docker Compose不可用，请先安装或确保Docker已启动")
            raise ComposeError("Docker Compose不可用，请先安装或确保Docker已启动")
        
        # 检查compose文件是否存在
        if not os.path.isfile(compose_file):
            error(f"Docker Compose文件不存在: {compose_file}")
            raise ComposeError(f"Docker Compose文件不存在: {compose_file}")
        
        # 准备命令
        compose_cmd = get_compose_cmd()
        cmd_parts = [compose_cmd, "-f", compose_file]
        
        # 添加项目名称
        if project_name:
            if compose_cmd == "docker-compose":
                cmd_parts.extend(["-p", project_name])
            else:
                cmd_parts.extend(["--project-name", project_name])
        
        # 如果需要构建
        if build:
            build_cmd = cmd_parts.copy()
            build_cmd.append("build")
            
            # 如果指定了特定服务，只构建这些服务
            if services:
                build_cmd.extend(services)
                
            info(f"构建Docker镜像: {' '.join(build_cmd)}")
            run_command(" ".join(build_cmd), verbose=True)
        
        # 准备启动命令
        cmd_parts.append("up")
        
        # 设置是否在后台运行
        if detached:
            cmd_parts.append("-d")
        
        # 如果指定了特定服务，只启动这些服务
        if services:
            cmd_parts.extend(services)
        
        # 执行启动命令
        info(f"启动Docker Compose服务: {' '.join(cmd_parts)}")
        run_command(" ".join(cmd_parts), verbose=True)
        
        success("Docker Compose服务已启动")
        return True
        
    except Exception as e:
        error(f"启动Docker Compose服务失败: {str(e)}")
        raise ComposeError(f"启动Docker Compose服务失败: {str(e)}")
