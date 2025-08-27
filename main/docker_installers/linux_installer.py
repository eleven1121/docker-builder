#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Linux系统的Docker安装器实现
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 Python 模块搜索路径中
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared import info, warning, error, success, run_command, CommandError
from .base_installer import BaseDockerInstaller, DockerInstallError


class LinuxDockerInstaller(BaseDockerInstaller):
    """Linux系统的Docker安装器实现"""
    
    def update_system(self):
        """
        更新Linux系统
        
        Returns:
            bool: 更新成功返回True
            
        Raises:
            DockerInstallError: 如果更新失败
        """
        try:
            info("======== Step 1: 更新系统 ========")
            run_command("sudo yum update -y")
            run_command("sudo yum clean all")
            success("系统更新完成")
            return True
        except CommandError as e:
            error(f"系统更新失败: {str(e)}")
            raise DockerInstallError(f"系统更新失败: {str(e)}")
    
    def install_dependencies(self):
        """
        安装Docker所需依赖
        
        Returns:
            bool: 安装依赖成功返回True
            
        Raises:
            DockerInstallError: 如果安装依赖失败
        """
        try:
            info("======== Step 2: 安装Docker所需依赖 ========")
            
            info("安装 dnf-utils")
            run_command("sudo yum install -y dnf-utils")
            
            info("安装 device-mapper-persistent-data")
            run_command("sudo yum install -y device-mapper-persistent-data")
            
            info("安装 lvm2")
            run_command("sudo yum install -y lvm2")
            
            success("所有依赖安装完成")
            return True
        except CommandError as e:
            error(f"安装依赖失败: {str(e)}")
            raise DockerInstallError(f"安装依赖失败: {str(e)}")
    
    def install_docker_engine(self):
        """
        安装Docker引擎
        
        Returns:
            bool: 安装Docker引擎成功返回True
            
        Raises:
            DockerInstallError: 如果安装Docker引擎失败
        """
        try:
            info("======== Step 3: 安装Docker引擎 ========")
            
            # 检查是否已安装 docker-ce-cli
            check_result = run_command("rpm -q docker-ce-cli", check=False, verbose=False)
            
            if check_result.returncode == 0:
                info("检测到已安装 docker-ce-cli，正在卸载...")
                run_command("sudo yum remove -y docker-ce-cli")
                success("docker-ce-cli 卸载完成")
                
            run_command("sudo yum install -y docker")
            success("Docker引擎安装完成")
            return True
        except CommandError as e:
            error(f"Docker引擎安装失败: {str(e)}")
            raise DockerInstallError(f"Docker引擎安装失败: {str(e)}")
    
    def install_docker_compose(self):
        """
        安装Docker Compose插件
        
        Returns:
            bool: 安装Docker Compose成功返回True
            
        Raises:
            DockerInstallError: 如果安装Docker Compose失败
        """
        try:
            info("======== Step 4: 安装Docker Compose插件 ========")
            run_command("sudo yum install -y docker-compose")
            success("Docker Compose安装完成")
            return True
        except CommandError as e:
            error(f"Docker Compose安装失败: {str(e)}")
            raise DockerInstallError(f"Docker Compose安装失败: {str(e)}")
    
    def configure_docker(self):
        """
        配置Docker镜像加速等
        
        Returns:
            bool: 配置成功返回True
            
        Raises:
            DockerInstallError: 如果配置失败
        """
        try:
            info("======== Step 5: 配置腾讯云镜像加速 ========")
            
            # 确保目录存在
            run_command("sudo mkdir -p /etc/docker")
            
            # 创建或更新配置文件
            mirror_config = {
                "registry-mirrors": ["https://mirror.ccs.tencentyun.com"]
            }
            
            # 将配置转为JSON并写入文件
            config_json = json.dumps(mirror_config, indent=2)
            
            # 使用临时文件并sudo移动到目标位置
            with open("/tmp/docker_daemon.json", "w") as f:
                f.write(config_json)
            
            run_command("sudo mv /tmp/docker_daemon.json /etc/docker/daemon.json")
            success("腾讯云镜像加速配置完成")
            return True
        except Exception as e:
            error(f"配置镜像加速失败: {str(e)}")
            raise DockerInstallError(f"配置镜像加速失败: {str(e)}")
    
    def start_docker_service(self):
        """
        启动Docker服务
        
        Returns:
            bool: 启动Docker服务成功返回True
            
        Raises:
            DockerInstallError: 如果启动Docker服务失败
        """
        try:
            info("======== Step 6: 启动Docker服务 ========")
            run_command("sudo systemctl enable docker")
            run_command("sudo systemctl restart docker")
            
            # 验证Docker状态
            result = run_command("sudo systemctl status docker", verbose=True, preserve_color=True)
            
            if "active (running)" in result.stdout.lower():
                success("Docker服务已成功启动并设置为开机自启")
            else:
                raise DockerInstallError("Docker服务启动失败")
                
            return True
        except CommandError as e:
            error(f"启动Docker服务失败: {str(e)}")
            raise DockerInstallError(f"启动Docker服务失败: {str(e)}")
    
    def install_docker(self):
        """
        安装Docker的主方法，调用install_docker_full实现
        
        Returns:
            bool: 安装成功返回True
            
        Raises:
            DockerInstallError: 如果安装失败
        """
        return self.install_docker_full()
