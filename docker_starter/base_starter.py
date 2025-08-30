#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker启动器的基础抽象类
定义所有启动器必须实现的接口方法
"""

import abc
import sys
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, warning, success, debug


class DockerStartError(Exception):
    """Docker启动过程中遇到的异常"""
    pass


class BaseDockerStarter(abc.ABC):
    """Docker启动器的基础抽象类"""
    
    @abc.abstractmethod
    def start_docker(self):
        """
        启动Docker服务的方法，由子类实现
        
        Returns:
            bool: 启动成功返回True
            
        Raises:
            DockerStartError: 如果启动失败
        """
        pass
    
    @abc.abstractmethod
    def stop_docker(self):
        """
        停止Docker服务的方法，由子类实现
        
        Returns:
            bool: 停止成功返回True
            
        Raises:
            DockerStartError: 如果停止失败
        """
        pass
    
    @abc.abstractmethod
    def restart_docker(self):
        """
        重启Docker服务的方法，由子类实现
        
        Returns:
            bool: 重启成功返回True
            
        Raises:
            DockerStartError: 如果重启失败
        """
        pass
    
    @abc.abstractmethod
    def get_docker_status(self):
        """
        获取Docker服务状态的方法，由子类实现
        
        Returns:
            str: Docker服务状态描述，如"running"、"stopped"等
        """
        pass
    
    @abc.abstractmethod
    def is_docker_running(self):
        """
        检查Docker是否正在运行的方法，由子类实现
        
        Returns:
            bool: 如果Docker正在运行返回True，否则返回False
        """
        pass
