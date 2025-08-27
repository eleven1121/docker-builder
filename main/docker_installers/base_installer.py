#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker安装器的基础抽象类
定义所有安装器必须实现的接口方法
"""

import abc
from shared import info, success, error, warning, debug


class DockerInstallError(Exception):
    """Docker安装过程中遇到的异常"""
    pass


class BaseDockerInstaller(abc.ABC):
    """Docker安装器的基础抽象类"""
    
    @abc.abstractmethod
    def install_docker(self):
        """
        安装Docker的主方法，由子类实现
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
        """
        pass
    
    @abc.abstractmethod
    def update_system(self):
        """
        更新系统的方法，由子类实现
        
        Returns:
            bool: 更新成功返回True
            
        Raises:
            DockerInstallError: 如果更新失败
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
    def install_docker_compose(self):
        """
        安装Docker Compose的方法，由子类实现
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
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
    def start_docker_service(self):
        """
        启动Docker服务的方法，由子类实现
        
        Returns:
            bool: 启动成功返回True
            
        Raises:
            DockerInstallError: 如果启动失败
        """
        pass
    
    def install_docker_full(self):
        """
        执行完整的Docker安装流程
        此方法调用各个子方法完成完整安装
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装过程中任何步骤失败
        """
        try:
            info("开始Docker安装流程...")
            
            # 执行安装的各个步骤
            self.update_system()
            self.install_dependencies()
            self.install_docker_engine()
            self.install_docker_compose()
            self.configure_docker()
            self.start_docker_service()
            
            success("Docker安装成功完成！")
            return True
        except DockerInstallError as e:
            error(f"Docker安装失败: {str(e)}")
            raise  # 重新抛出异常给调用者
        except Exception as e:
            error(f"Docker安装过程中发生未预期的异常: {str(e)}")
            raise DockerInstallError(f"Docker安装过程中发生未预期的异常: {str(e)}")
