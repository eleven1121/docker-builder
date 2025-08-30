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


class ComposeError(Exception):
    """Docker Compose操作异常"""
    pass


class ComposeManager:
    """
    Docker Compose 管理器工厂类
    根据当前操作系统实例化并返回适当的Compose管理器
    """
    
    @staticmethod
    def get_compose_manager():
        """
        获取适合当前操作系统的Docker Compose管理器
        
        Returns:
            BaseComposeManager: 返回一个Docker Compose管理器实例
            
        Raises:
            ComposeError: 如果当前操作系统不支持则抛出异常
        """
        os_type = platform.system().lower()
        
        try:
            if os_type == "linux":
                # 延迟导入以避免循环导入
                from docker_compose.linux_compose import LinuxComposeManager
                return LinuxComposeManager()
                
            elif os_type == "darwin":
                # 延迟导入以避免循环导入
                from docker_compose.mac_compose import MacComposeManager
                return MacComposeManager()
                
            else:
                error(f"不支持的操作系统: {os_type}")
                raise ComposeError(f"不支持的操作系统: {os_type}")
                
        except ImportError as e:
            error(f"导入Compose管理器时出错: {str(e)}")
            raise ComposeError(f"导入Compose管理器时出错: {str(e)}")
    
    @staticmethod
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
        compose_manager = ComposeManager.get_compose_manager()
        
        # 检查是否已安装
        if not force and compose_manager.is_compose_installed():
            current_version = compose_manager.get_compose_version()
            info(f"Docker Compose已安装（版本: {current_version}），无需重新安装")
            return False
            
        try:
            return compose_manager.install_compose(version)
        except Exception as e:
            error(f"安装Docker Compose失败: {str(e)}")
            raise ComposeError(f"安装Docker Compose失败: {str(e)}")
    
    @staticmethod
    def is_compose_running():
        """
        检查Docker Compose是否正常运行
        
        Returns:
            bool: 如果Docker Compose可用且可以正常运行，返回True，否则返回False
        """
        try:
            compose_manager = ComposeManager.get_compose_manager()
            return compose_manager.is_compose_installed()
        except Exception as e:
            debug(f"检查Docker Compose状态时出错: {str(e)}")
            return False
    
    @staticmethod
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
        
        try:
            compose_manager = ComposeManager.get_compose_manager()
            return compose_manager.reinstall_compose(version)
        except Exception as e:
            error(f"重新安装Docker Compose失败: {str(e)}")
            raise ComposeError(f"重新安装Docker Compose失败: {str(e)}")
            
    @staticmethod
    def get_compose_version():
        """
        获取Docker Compose版本
        
        Returns:
            str: Docker Compose版本号，如果未安装则返回None
        """
        try:
            compose_manager = ComposeManager.get_compose_manager()
            return compose_manager.get_compose_version()
        except Exception as e:
            debug(f"获取Docker Compose版本时出错: {str(e)}")
            return None
            
    @staticmethod
    def get_compose_cmd():
        """
        获取docker-compose命令
        
        Returns:
            str: docker-compose命令
        """
        try:
            compose_manager = ComposeManager.get_compose_manager()
            return compose_manager.get_compose_cmd()
        except Exception as e:
            debug(f"获取docker-compose命令时出错: {str(e)}")
            return "docker compose"  # 默认使用新版命令格式

@staticmethod
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
        compose_manager = ComposeManager.get_compose_manager()
        return compose_manager.start_service_by_compose(
            compose_file=compose_file,
            project_name=project_name,
            services=services,
            detached=detached,
            build=build
        )
    except Exception as e:
        error(f"启动Docker Compose服务失败: {str(e)}")
        raise ComposeError(f"启动Docker Compose服务失败: {str(e)}")

# 添加到ComposeManager类中
ComposeManager.start_service_by_compose = start_service_by_compose
