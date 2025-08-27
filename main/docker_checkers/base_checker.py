#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker检查器基类
定义Docker检查器的接口和通用方法
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error, success, run_command, CommandError


class DockerCheckError(Exception):
    """Docker检查过程中遇到的异常"""
    pass


class DockerChecker(ABC):
    """Docker检查器抽象基类"""
    
    @abstractmethod
    def check_docker_installed(self):
        """
        检查Docker是否已安装
        
        Returns:
            bool: 如果Docker已安装返回True
            
        Raises:
            DockerCheckError: 如果Docker未安装
        """
        pass
        
    @abstractmethod
    def check_docker_running(self):
        """
        检查Docker服务是否正在运行
        
        Returns:
            bool: 如果Docker服务正在运行返回True
            
        Raises:
            DockerCheckError: 如果Docker服务未运行
        """
        pass
        
    @abstractmethod
    def check_docker_functional(self):
        """
        检查Docker的基本功能是否正常
        
        Returns:
            bool: 如果Docker功能正常返回True
            
        Raises:
            DockerCheckError: 如果Docker功能异常
        """
        pass
        
    def check_docker(self):
        """
        主方法: 检查Docker的安装、运行状态和功能
        
        Returns:
            bool: 所有检查都通过返回True
            
        Raises:
            DockerCheckError: 如果任何检查失败
        """
        try:
            info("开始检查Docker状态...")
            
            # 逐个执行检查，任一检查失败都会抛出异常
            self.check_docker_installed()
            self.check_docker_running()
            self.check_docker_functional()
            
            success("Docker检查完成，已安装、运行中、功能正常")
            return True
        except DockerCheckError as e:
            error(f"Docker检查失败: {str(e)}")
            raise  # 重新抛出异常给调用者
        except Exception as e:
            error(f"Docker检查过程中发生未预期的异常: {str(e)}")
            raise DockerCheckError(f"Docker检查过程中发生未预期的异常: {str(e)}")
