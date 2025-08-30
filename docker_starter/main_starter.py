#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker启动器主类
根据不同操作系统创建对应的启动器实例
"""

import os
import sys
import platform
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, warning, success, debug

from docker_starter.base_starter import DockerStartError
from docker_starter.linux_starter import LinuxDockerStarter
from docker_starter.mac_starter import MacDockerStarter


class DockerStarter:
    """Docker启动器工厂类，根据系统创建对应的启动器实例"""
    
    def __init__(self):
        """初始化Docker启动器，根据当前系统类型选择对应的启动器"""
        self.platform = platform.system().lower()
        
        if self.platform == "linux":
            debug("检测到Linux系统，使用Linux启动器")
            self.starter = LinuxDockerStarter()
        elif self.platform == "darwin":
            debug("检测到Mac系统，使用Mac启动器")
            self.starter = MacDockerStarter()
        else:
            error(f"不支持的操作系统: {self.platform}")
            raise DockerStartError(f"不支持的操作系统: {self.platform}")
    
    def is_docker_running(self):
        """
        检查Docker是否正在运行，代理到具体实现类
        
        Returns:
            bool: 如果Docker正在运行返回True，否则返回False
        """
        return self.starter.is_docker_running()
    
    def get_docker_status(self):
        """
        获取Docker服务状态，代理到具体实现类
        
        Returns:
            str: Docker服务状态描述
        """
        return self.starter.get_docker_status()
    
    def start_docker(self):
        """
        启动Docker服务，代理到具体实现类
        
        Returns:
            bool: 启动成功返回True
            
        Raises:
            DockerStartError: 如果启动失败
        """
        try:
            info("开始启动Docker...")
            
            # 检查Docker是否已经在运行
            if self.is_docker_running():
                success("Docker已启动 | 无需重复启动")
                return True
                
            # 启动Docker
            result = self.starter.start_docker()
            
            # 验证启动结果
            if result and self.is_docker_running():
                success("Docker已成功启动")
                return True
            else:
                warning("Docker似乎已启动，但状态验证失败")
                return False
                
        except DockerStartError as e:
            error(f"Docker启动失败: {str(e)}")
            raise
        except Exception as e:
            error(f"Docker启动过程中发生未预期的错误: {str(e)}")
            raise DockerStartError(f"Docker启动失败: {str(e)}")
    
    def stop_docker(self):
        """
        停止Docker服务，代理到具体实现类
        
        Returns:
            bool: 停止成功返回True
            
        Raises:
            DockerStartError: 如果停止失败
        """
        try:
            info("开始停止Docker...")
            
            # 检查Docker是否在运行
            if not self.is_docker_running():
                info("Docker未在运行，无需停止")
                return True
                
            # 停止Docker
            result = self.starter.stop_docker()
            
            # 验证停止结果
            if result and not self.is_docker_running():
                success("Docker已成功停止")
                return True
            else:
                warning("Docker停止操作已执行，但状态验证失败")
                return False
                
        except DockerStartError as e:
            error(f"Docker停止失败: {str(e)}")
            raise
        except Exception as e:
            error(f"Docker停止过程中发生未预期的错误: {str(e)}")
            raise DockerStartError(f"Docker停止失败: {str(e)}")
    
    def restart_docker(self):
        """
        重启Docker服务，代理到具体实现类
        
        Returns:
            bool: 重启成功返回True
            
        Raises:
            DockerStartError: 如果重启失败
        """
        try:
            info("开始重启Docker...")
            
            # 重启Docker
            result = self.starter.restart_docker()
            
            # 验证重启结果
            if result and self.is_docker_running():
                success("Docker已成功重启并正常运行")
                return True
            else:
                warning("Docker重启操作已执行，但状态验证失败")
                return False
                
        except DockerStartError as e:
            error(f"Docker重启失败: {str(e)}")
            raise
        except Exception as e:
            error(f"Docker重启过程中发生未预期的错误: {str(e)}")
            raise DockerStartError(f"Docker重启失败: {str(e)}")
