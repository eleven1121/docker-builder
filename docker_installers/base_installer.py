#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker安装器的基础抽象类
定义所有安装器必须实现的接口方法
"""

import abc
import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, warning, success, debug


class DockerInstallError(Exception):
    """Docker安装过程中遇到的异常"""
    pass


class BaseDockerInstaller(abc.ABC):
    """Docker安装器的基础抽象类"""
    
    @abc.abstractmethod
    def install_docker_engine(self):
        """
        安装Docker引擎的方法，由子类实现
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
        """
        pass
    
    @abc.abstractmethod
    def install_dependencies(self):
        """
        安装依赖项的方法，由子类实现
        
        Returns:
            bool: 安装依赖成功返回True
            
        Raises:
            DockerInstallError: 如果安装依赖失败
        """
        pass
    
    
    @abc.abstractmethod
    def configure_docker(self):
        """
        配置Docker的方法，由子类实现
        包括镜像加速等配置
        
        Returns:
            bool: 配置成功返回True
            
        Raises:
            DockerInstallError: 如果配置失败
        """
        pass
    
    @abc.abstractmethod
    def uninstall_docker(self):
        """
        卸载Docker的方法，由子类实现
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerInstallError: 如果卸载失败
        """
        pass
    
    @abc.abstractmethod
    def is_docker_installed(self):
        """
        检查Docker是否已安装
        
        Returns:
            bool: 如果Docker已安装返回True，否则返回False
        """
        pass
