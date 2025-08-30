#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker安装器主类
根据不同操作系统创建对应的安装器实例
"""

import os
import sys
import platform
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).absolute().parent.parent))

from shared.logger import info, error, warning, success, debug

from docker_installers.base_installer import DockerInstallError
from docker_installers.linux_installer import LinuxDockerInstaller
from docker_installers.mac_installer import MacDockerInstaller


class DockerInstaller:
    """Docker安装器工厂类，根据系统创建对应的安装器实例"""
    
    def __init__(self):
        """初始化Docker安装器，根据当前系统类型选择对应的安装器"""
        self.platform = platform.system().lower()
        
        if self.platform == "linux":
            debug("检测到Linux系统，使用Linux安装器")
            self.installer = LinuxDockerInstaller()
        elif self.platform == "darwin":
            debug("检测到Mac系统，使用Mac安装器")
            self.installer = MacDockerInstaller()
        else:
            error(f"不支持的操作系统: {self.platform}")
            raise DockerInstallError(f"不支持的操作系统: {self.platform}")
    
    def is_docker_installed(self):
        """
        检查Docker是否已安装并正常运行，代理到具体实现类
        
        Returns:
            bool: 如果Docker已安装并正常运行返回True，否则返回False
        """
        return self.installer.is_docker_installed()
    
    def install_docker_full(self):
        """
        安装Docker完整流程
        
        如果Docker已安装并正常运行，则直接返回True
        否则，依次执行安装依赖、安装Docker引擎、配置Docker
        并最终验证安装结果
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装过程中任何步骤失败
        """
        try:
            info("开始Docker安装流程...")
            
            # 首先检查Docker是否已安装
            if self.is_docker_installed():
                success("Docker已安装 | 无需重复安装")
                return True
                
            # 依次执行安装步骤
            info("Docker未安装或未正常运行，开始安装流程")
            
            # 1. 安装依赖
            if not self.installer.install_dependencies():
                raise DockerInstallError("安装依赖失败")
                
            # 2. 安装Docker引擎
            if not self.installer.install_docker_engine():
                raise DockerInstallError("安装Docker引擎失败")
            
            # 3. 配置Docker
            if not self.installer.configure_docker():
                raise DockerInstallError("配置Docker失败")
                
            # 最终验证Docker安装
            info("安装流程完成，正在验证Docker...")
            if self.is_docker_installed():
                success("Docker已成功安装")
                return True
            else:
                warning("Docker未安装成功")
                raise DockerInstallError("Docker安装失败")
                
        except DockerInstallError as e:
            error(f"Docker安装失败: {str(e)}")
            raise
        except Exception as e:
            error(f"Docker安装过程中发生未预期的错误: {str(e)}")
            raise DockerInstallError(f"Docker安装失败: {str(e)}")
    
    def uninstall_docker(self):
        """
        卸载Docker，代理到具体实现类
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerInstallError: 如果卸载失败
        """
        return self.installer.uninstall_docker()
