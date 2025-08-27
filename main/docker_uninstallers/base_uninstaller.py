#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docker卸载器的基础抽象类
定义所有卸载器必须实现的接口方法
"""

import abc
from shared import info, success, error, warning, debug


class DockerUninstallError(Exception):
    """Docker卸载过程中遇到的异常"""
    pass


class BaseDockerUninstaller(abc.ABC):
    """Docker卸载器的基础抽象类"""
    
    @abc.abstractmethod
    def uninstall_docker(self):
        """
        卸载Docker的主方法，由子类实现
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerUninstallError: 如果卸载失败
        """
        pass
    
    @abc.abstractmethod
    def stop_docker_service(self):
        """
        停止Docker服务的方法，由子类实现
        
        Returns:
            bool: 停止成功返回True
            
        Raises:
            DockerUninstallError: 如果停止失败
        """
        pass
    
    @abc.abstractmethod
    def remove_docker_packages(self):
        """
        卸载Docker包的方法，由子类实现
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerUninstallError: 如果卸载失败
        """
        pass
    
    @abc.abstractmethod
    def remove_docker_data(self):
        """
        移除Docker数据的方法，由子类实现
        
        Returns:
            bool: 移除成功返回True
            
        Raises:
            DockerUninstallError: 如果移除失败
        """
        pass
    
    @abc.abstractmethod
    def clean_system(self):
        """
        清理系统残留的方法，由子类实现
        
        Returns:
            bool: 清理成功返回True
            
        Raises:
            DockerUninstallError: 如果清理失败
        """
        pass
    
    def uninstall_docker_full(self):
        """
        执行完整的Docker卸载流程
        此方法调用各个子方法完成完整卸载
        
        Returns:
            bool: 卸载成功返回True
            
        Raises:
            DockerUninstallError: 如果卸载过程中任何步骤失败
        """
        try:
            info("开始Docker卸载流程...")
            
            # 执行卸载的各个步骤
            self.stop_docker_service()
            self.remove_docker_packages()
            self.remove_docker_data()
            self.clean_system()
            
            success("Docker卸载成功完成！")
            return True
        except DockerUninstallError as e:
            error(f"Docker卸载失败: {str(e)}")
            raise  # 重新抛出异常给调用者
        except Exception as e:
            error(f"Docker卸载过程中发生未预期的异常: {str(e)}")
            raise DockerUninstallError(f"Docker卸载过程中发生未预期的异常: {str(e)}")
