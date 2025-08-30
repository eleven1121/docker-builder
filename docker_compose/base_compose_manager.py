#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker Compose 管理器基类
定义所有Compose管理器必须实现的抽象方法
"""

import abc
import sys
from pathlib import Path

# 添加项目根目录到Python模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, debug, warning, success
from docker_compose.compose_manager import ComposeError


class BaseComposeManager(abc.ABC):
    """Docker Compose管理器的基类"""
    
    @abc.abstractmethod
    def install_compose(self, version=None):
        """
        安装Docker Compose
        
        Args:
            version: 指定要安装的版本，如果为None则安装最新版本
            
        Returns:
            bool: 安装成功返回True
            
        Raises:
            ComposeError: 安装失败时抛出异常
        """
        pass
    
    @abc.abstractmethod
    def reinstall_compose(self, version=None):
        """
        重新安装Docker Compose
        
        Args:
            version: 指定要安装的版本，如果为None则安装最新版本
            
        Returns:
            bool: 重新安装成功返回True
            
        Raises:
            ComposeError: 重新安装失败时抛出异常
        """
        pass
    
    @abc.abstractmethod
    def is_compose_installed(self):
        """
        检查Docker Compose是否已安装
        
        Returns:
            bool: 如果Docker Compose已安装返回True，否则返回False
        """
        pass
    
    @abc.abstractmethod
    def get_compose_version(self):
        """
        获取Docker Compose版本
        
        Returns:
            str: Docker Compose版本号，如果未安装则返回None
        """
        pass
    
    @abc.abstractmethod
    def get_compose_cmd(self):
        """
        获取docker-compose命令
        
        Returns:
            str: docker-compose命令
        """
        pass
        
    def start_service_by_compose(self, compose_file, project_name=None, services=None, detached=True, build=False):
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
        from shared.run_command import run_command, CommandError
        import os
        
        try:
            # 检查Docker Compose是否可用
            if not self.is_compose_installed():
                error("Docker Compose不可用，请先安装或确保Docker已启动")
                raise ComposeError("Docker Compose不可用，请先安装或确保Docker已启动")
            
            # 检查compose文件是否存在
            if not os.path.isfile(compose_file):
                error(f"Docker Compose文件不存在: {compose_file}")
                raise ComposeError(f"Docker Compose文件不存在: {compose_file}")
            
            # 准备命令
            compose_cmd = self.get_compose_cmd()
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
